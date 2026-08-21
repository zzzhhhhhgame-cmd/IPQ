/*
 * =====================================================================
 *  IPQ 研究 · 双电机差速的 PID 抑制
 * =====================================================================
 *  目标：左右轮各自用编码器测速，经 PID 闭环跟踪同一目标转速，
 *        消除开环 PWM 下 ~5% 量级的轮速差（电机/摩擦个体差异）。
 *
 *  硬件与接线：与 ipq_robot_test 完全相同（wiring-checklist v3.3）
 *  依赖库：无（仅 ESP32 核心自带 Wire / SPI / SD）
 *
 *  研究用法：
 *   1. 'w' 起步后按 'o' 切换 开环↔闭环，观察 Δrpm 与 gyrZ 的变化；
 *   2. 串口改 kp/ki/kd/ff 参数做调参实验（掉电丢失，记到本子上）；
 *   3. 'z' 清零编码器后 'w' 跑 5 秒 'x'，得到阶跃响应曲线（SD 有完整记录）；
 *   4. ff 设为 0 可对比"纯 PID"与"前馈+PID"的收敛速度。
 *
 *  串口命令（115200）：
 *    w/s/a/d 前进/后退/左转/右转   x 刹车   c 滑行   z 编码器清零
 *    0~9 目标转速 = 数字×15 rpm（3 → 45）  + / - 目标 ±5 rpm
 *    r60     直接设目标转速(rpm)
 *    kp2.0 / ki0.1 / kd0.05 / ff1.3   改 PID 参数（如 ki0 = 关积分）
 *    o       开环 / 闭环 切换（研究对照用）
 *    p 立即打印一帧   t 遥测开关   e 串口CSV输出   v8.06 电池电压替代值   h 帮助
 * =====================================================================
 */

#include <Wire.h>
#include <SPI.h>
#include <SD.h>

/* ---------------- 引脚（wiring-checklist v3.3）---------------- */
static const uint8_t PIN_AIN1    = 23;   // 左电机 方向
static const uint8_t PIN_AIN2    = 19;   // 左电机 PWM
static const uint8_t PIN_BIN1    = 18;   // 右电机 方向
static const uint8_t PIN_BIN2    = 16;   // 右电机 PWM
static const uint8_t PIN_ENC_LA  = 34;
static const uint8_t PIN_ENC_LB  = 35;
static const uint8_t PIN_ENC_RA  = 32;
static const uint8_t PIN_ENC_RB  = 33;
static const uint8_t PIN_SDA     = 21;
static const uint8_t PIN_SCL     = 22;
static const uint8_t PIN_SD_SCK  = 14;
static const uint8_t PIN_SD_MOSI = 15;
static const uint8_t PIN_SD_MISO = 2;
static const uint8_t PIN_SD_CS   = 27;

static const uint8_t ADDR_INA = 0x40;

static const char CSV_HEADER[] = "ms,tgt,rpmL,rpmR,pwmL,pwmR,gyrZ,busV,curA,powW";

/* ---------------- 可调参数 ---------------- */
#define PWM_FREQ_HZ   20000
#define R_SHUNT       0.1f    // INA226 采样电阻（丝印 R100=0.1Ω）
#define ENC_PPR       11      // JGB37-520B 编码器 PPR
#define GEAR_RATIO    30      // 减速比 1:30 → 轮轴 330 计数/圈
#define ENC_L_INVERT  0       // 前进时左计数为负 → 改 1
#define ENC_R_INVERT  0
#define MOT_L_INVERT  0       // 'w' 时左轮反转 → 改 1
#define MOT_R_INVERT  0
#define TSAMP_MS      100     // 控制周期 100ms（转速量化 ≈1.8rpm，勿太短）
#define RPM_FILT_A    0.35f   // 转速低通系数（0~1，越小越平滑越迟钝）
#define I_MAX         120.0f  // 积分限幅（抗饱和，PWM 当量）

/* ---------------- PID 状态（串口随时改）---------------- */
static float kp = 2.0f;       // 比例：1 rpm 误差 → 几个 PWM 当量
static float ki = 0.15f;      // 积分
static float kd = 0.0f;       // 微分（默认关；量化噪声大，慎用）
static float ff = 1.3f;       // 前馈：PWM/rpm（0 = 纯 PID）
static float targetRpm = 45;  // 目标转速（幅值）
static bool  pidOn = true;    // false = 开环（两轮同 PWM，对照组）

/* =====================================================================
 *  LEDC PWM 封装（兼容核心 2.x / 3.x）
 * ===================================================================== */
#if defined(ESP_ARDUINO_VERSION) && ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
static void pwmSetup(uint8_t pin)            { ledcAttach(pin, PWM_FREQ_HZ, 8); }
static void pwmWrite(uint8_t pin, uint32_t d){ ledcWrite(pin, d); }
#else
static uint8_t pwmChOf(uint8_t pin) { return (pin == PIN_AIN2) ? 0 : 1; }
static void pwmSetup(uint8_t pin)   { ledcSetup(pwmChOf(pin), PWM_FREQ_HZ, 8); ledcAttachPin(pin, pwmChOf(pin)); }
static void pwmWrite(uint8_t pin, uint32_t d) { ledcWrite(pwmChOf(pin), d); }
#endif

/* =====================================================================
 *  DRV8833：IN1=方向(数字)、IN2=PWM（与接线清单 E/F 组一致）
 * ===================================================================== */
static void motorWrite(uint8_t dirPin, uint8_t pwmPin, int speed)
{
  if (speed > 0) {
    digitalWrite(dirPin, HIGH);
    pwmWrite(pwmPin, 255 - speed);
  } else if (speed < 0) {
    digitalWrite(dirPin, LOW);
    pwmWrite(pwmPin, (uint32_t)(-speed));
  } else {
    digitalWrite(dirPin, LOW);
    pwmWrite(pwmPin, 0);
  }
}

static void setMotors(int l, int r)
{
#if MOT_L_INVERT
  l = -l;
#endif
#if MOT_R_INVERT
  r = -r;
#endif
  motorWrite(PIN_AIN1, PIN_AIN2, l);
  motorWrite(PIN_BIN1, PIN_BIN2, r);
}

static void brakeAll()
{
  digitalWrite(PIN_AIN1, HIGH); pwmWrite(PIN_AIN2, 255);
  digitalWrite(PIN_BIN1, HIGH); pwmWrite(PIN_BIN2, 255);
}

/* ---------------- 运动指令状态 ---------------- */
static int8_t dirL = 0, dirR = 0;    // -1/0/+1，来自 w/s/a/d

/* =====================================================================
 *  编码器
 * ===================================================================== */
static volatile int32_t encCountL = 0;
static volatile int32_t encCountR = 0;

void IRAM_ATTR isrEncL() { digitalRead(PIN_ENC_LB) ? encCountL++ : encCountL--; }
void IRAM_ATTR isrEncR() { digitalRead(PIN_ENC_RB) ? encCountR++ : encCountR--; }

/* =====================================================================
 *  I²C 读写 + INA226（电流/电压；母线通道坏则电压用替代值）
 * ===================================================================== */
static bool    inaOK = false;
static uint32_t inaRetryAt = 0;
static float   vBatFallback = 8.0f;

static bool i2cWrite8(uint8_t addr, uint8_t reg, uint8_t val)
{
  Wire.beginTransmission(addr);
  Wire.write(reg); Wire.write(val);
  return Wire.endTransmission() == 0;
}

static bool i2cWrite16(uint8_t addr, uint8_t reg, uint16_t val)
{
  Wire.beginTransmission(addr);
  Wire.write(reg); Wire.write(val >> 8); Wire.write(val & 0xFF);
  return Wire.endTransmission() == 0;
}

static int16_t i2cRead16(uint8_t addr, uint8_t reg, bool &ok)
{
  Wire.beginTransmission(addr); Wire.write(reg);
  if (Wire.endTransmission(false) != 0) { ok = false; return 0; }
  if (Wire.requestFrom((uint8_t)addr, (uint8_t)2) != 2)         { ok = false; return 0; }
  uint16_t v = ((uint16_t)Wire.read() << 8) | Wire.read();
  ok = true;
  return (int16_t)v;
}

static bool i2cRead8(uint8_t addr, uint8_t reg, uint8_t &out)
{
  Wire.beginTransmission(addr); Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((uint8_t)addr, (uint8_t)1) != 1) return false;
  out = Wire.read();
  return true;
}

static bool inaInit()
{
  bool ok = i2cWrite16(ADDR_INA, 0x00, 0x4587);   // 16 次平均，分流+母线连续
  bool okR;
  uint16_t cfg = (uint16_t)i2cRead16(ADDR_INA, 0x00, okR);
  Serial.printf("  [INA诊断] CFG回读=0x%04X %s\n", cfg, ok ? "OK" : "失败");
  return ok;
}

/* =====================================================================
 *  IMU（MPU6050 / LSM6 兼容自动识别）+ 陀螺零偏
 * ===================================================================== */
static bool    imuOK    = false;
static bool    imuIsLSM = false;
static uint8_t imuAddr  = 0;
static float   gyroBias[3] = {0, 0, 0};

static bool imuRead(int16_t a[3], int16_t &tRaw, int16_t g[3]);   // 前置声明

static bool imuInit()
{
  uint8_t v;
  for (uint8_t a = 0x6A; a <= 0x6B; a++) {          // LSM6 系（WHO_AM_I=0x0F）
    if (!i2cRead8(a, 0x0F, v)) continue;
    if (v == 0x6A || v == 0x6B || v == 0x6C) {
      imuAddr = a; imuIsLSM = true;
      bool ok = i2cWrite8(a, 0x12, 0x44);
      ok &= i2cWrite8(a, 0x10, 0x40);               // 104Hz ±2g
      ok &= i2cWrite8(a, 0x11, 0x40);               // 104Hz ±245dps
      delay(50);
      return ok;
    }
  }
  for (uint8_t a = 0x68; a <= 0x69; a++) {          // MPU6050（WHO_AM_I=0x75）
    if (!i2cRead8(a, 0x75, v) || v != 0x68) continue;
    imuAddr = a; imuIsLSM = false;
    bool ok = i2cWrite8(a, 0x6B, 0x01);
    ok &= i2cWrite8(a, 0x19, 0x04);
    ok &= i2cWrite8(a, 0x1A, 0x03);
    ok &= i2cWrite8(a, 0x1B, 0x00);
    ok &= i2cWrite8(a, 0x1C, 0x00);
    delay(50);
    return ok;
  }
  for (uint8_t a = 0x6A; a <= 0x6B; a++) {          // 兼容片盲试探：写 CTRL3_C 回读验证
    Wire.beginTransmission(a);
    if (Wire.endTransmission() != 0) continue;
    if (!i2cWrite8(a, 0x12, 0x44)) continue;
    uint8_t rb = 0;
    if (!i2cRead8(a, 0x12, rb) || rb != 0x44) continue;
    i2cWrite8(a, 0x10, 0x40);
    i2cWrite8(a, 0x11, 0x40);
    delay(60);
    imuAddr = a; imuIsLSM = true;
    return true;
  }
  return false;
}

static bool imuRead(int16_t a[3], int16_t &tRaw, int16_t g[3])
{
  Wire.beginTransmission(imuAddr);
  if (imuIsLSM) Wire.write(0x22);
  else          Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  uint8_t n = imuIsLSM ? 12 : 14;
  if (Wire.requestFrom((uint8_t)imuAddr, n) != n) return false;
  if (imuIsLSM) {
    for (int i = 0; i < 3; i++)
      g[i] = (int16_t)((uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8));
    for (int i = 0; i < 3; i++)
      a[i] = (int16_t)((uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8));
    Wire.beginTransmission(imuAddr); Wire.write(0x20);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((uint8_t)imuAddr, (uint8_t)2) != 2) return false;
    uint8_t lo = Wire.read(), hi = Wire.read();
    tRaw = (int16_t)((uint16_t)lo | ((uint16_t)hi << 8));
  } else {
    for (int i = 0; i < 3; i++)
      a[i] = ((int16_t)Wire.read() << 8) | Wire.read();
    tRaw = ((int16_t)Wire.read() << 8) | Wire.read();
    for (int i = 0; i < 3; i++)
      g[i] = ((int16_t)Wire.read() << 8) | Wire.read();
  }
  return true;
}

/* =====================================================================
 *  microSD：研究数据记录
 * ===================================================================== */
static File logFile;
static bool sdOK = false;
static uint8_t flushCnt = 0;

static void sdInit()
{
  SPI.begin(PIN_SD_SCK, PIN_SD_MISO, PIN_SD_MOSI, PIN_SD_CS);
  if (!SD.begin(PIN_SD_CS)) {
    Serial.println(F("SD 卡初始化失败（不影响其它功能；烧录时建议拔下 SD 模块）"));
    return;
  }
  char name[20];
  for (int i = 0; i < 1000; i++) {
    snprintf(name, sizeof(name), "/pid%03d.csv", i);
    if (!SD.exists(name)) break;
  }
  logFile = SD.open(name, FILE_WRITE);
  if (!logFile) { Serial.println(F("SD 卡无法创建日志文件")); return; }
  logFile.println(CSV_HEADER);
  logFile.flush();
  sdOK = true;
  Serial.printf("SD: 日志写入 %s\n", name);
}

/* =====================================================================
 *  速度测量 + 双轮 PID
 * ===================================================================== */
static int32_t lastCntL = 0, lastCntR = 0;
static float   rpmL = 0, rpmR = 0;          // 低通后转速（带符号）
static float   iL = 0, iR = 0;              // 积分累加
static float   prevL = 0, prevR = 0;        // 上拍转速（微分用）
static float   uL = 0, uR = 0;              // 本拍 PWM 输出（带符号）
static float   gyrZ = 0;                    // 陀螺 Z 轴（转向角速度）
static float   vBus = NAN, iMot = NAN, pMot = NAN;
static bool    vAssumed = false;
static bool    telemetryOn = true;
static bool    csvOut = false;        // e 命令：把 CSV 数据行同步输出到串口（无 SD 卡时用电脑记录）

static void resetPid()
{
  iL = iR = 0;
  prevL = rpmL;  prevR = rpmR;
}

/* 单轮 PID：返回带符号 PWM(-255..255)。T=带符号目标转速 */
static float pidStep(float T, float rpm, float &integ, float &prev)
{
  if (T == 0) { integ = 0; return 0; }
  float e  = T - rpm;
  float dt = TSAMP_MS / 1000.0f;
  float p  = kp * e;
  integ += ki * e * dt;                            // 积分
  if (integ >  I_MAX) integ =  I_MAX;              // 抗饱和
  if (integ < -I_MAX) integ = -I_MAX;
  float d  = -kd * (rpm - prev) / dt;              // 微分作用于测量值（避免目标阶跃踢）
  prev = rpm;
  float u = ff * T + p + integ + d;                // 前馈 + PID
  if (u >  255) u =  255;
  if (u < -255) u = -255;
  return u;
}

static void controlStep()
{
  /* --- 1. 转速测量（编码器差分 + 低通）--- */
  int32_t l = encCountL, r = encCountR;
  float dL = (float)(l - lastCntL);  lastCntL = l;
  float dR = (float)(r - lastCntR);  lastCntR = r;
  float k  = 60000.0f / TSAMP_MS / (ENC_PPR * GEAR_RATIO);
  float rawL = dL * k * (ENC_L_INVERT ? -1 : 1);
  float rawR = dR * k * (ENC_R_INVERT ? -1 : 1);
  rpmL += RPM_FILT_A * (rawL - rpmL);
  rpmR += RPM_FILT_A * (rawR - rpmR);

  /* --- 2. 传感器（陀螺 Z 轴 = 差速效果的独立判据；INA 供电参数）--- */
  int16_t a3[3], tRaw, g3[3];
  if (imuOK && imuRead(a3, tRaw, g3))
    gyrZ = (g3[2] - gyroBias[2]) * (imuIsLSM ? 8.75f / 1000 : 1.0f / 131.0f);
  else
    imuOK = false;

  if (!inaOK && inaRetryAt && (int32_t)(millis() - inaRetryAt) >= 0) {
    inaRetryAt = 0;
    if (i2cWrite16(ADDR_INA, 0x00, 0x4587)) { inaOK = true; Serial.println(F("!! INA226 已重新上线")); }
    else inaRetryAt = millis() + 10000;
  }
  if (inaOK) {
    bool ok;
    int16_t shunt = i2cRead16(ADDR_INA, 0x01, ok);
    if (!ok) { inaOK = false; inaRetryAt = millis() + 10000; }
    else     { iMot = (shunt * 2.5e-6f) / R_SHUNT; }
    int16_t bus = i2cRead16(ADDR_INA, 0x02, ok);
    if (ok) {
      vBus = bus * 0.00125f;
      vAssumed = (vBus < 0.5f);
      if (vAssumed) vBus = vBatFallback;
      pMot = vBus * iMot;
    } else if (!inaOK) { vBus = iMot = pMot = NAN; }
  }

  /* --- 3. 双轮控制 --- */
  float TL = dirL * targetRpm;
  float TR = dirR * targetRpm;
  if (pidOn) {
    uL = pidStep(TL, rpmL, iL, prevL);
    uR = pidStep(TR, rpmR, iR, prevR);
  } else {                                  // 开环对照：两轮同 PWM
    uL = ff * TL;  if (uL >  255) uL =  255;  if (uL < -255) uL = -255;
    uR = ff * TR;  if (uR >  255) uR =  255;  if (uR < -255) uR = -255;
  }
  if (dirL == 0 && dirR == 0) return;       // 停止状态保持刹车/滑行
  setMotors((int)uL, (int)uR);
}

/* ---------------- 遥测与记录 ---------------- */
static void printTelemetry()
{
  Serial.printf("[%6.1fs] %s T%+5.1f | L %5.1frpm u%+4.0f  R %5.1frpm u%+4.0f | d%+5.1frpm gyrZ %+5.1f | ",
                millis() / 1000.0, pidOn ? "PID" : "开环", targetRpm,
                rpmL, uL, rpmR, uR, rpmL - rpmR, gyrZ);
  if (!isnan(vBus))
    Serial.printf("bat %.2f%sV cur %.3fA pow %.2fW\n", vBus, vAssumed ? "*" : "", iMot, pMot);
  else
    Serial.println(F("bat  ----   cur  ----   pow  ----"));
}

static void appF(char *line, float v)
{
  char c[24];
  if (isnan(v)) strcat(line, ",");
  else { snprintf(c, sizeof(c), ",%.4f", v); strcat(line, c); }
}

static void buildCsvLine(char *line, size_t n)
{
  snprintf(line, n, "%lu", (unsigned long)millis());
  appF(line, targetRpm); appF(line, rpmL); appF(line, rpmR);
  appF(line, uL);        appF(line, uR);   appF(line, gyrZ);
  appF(line, vBus);      appF(line, iMot); appF(line, pMot);
  strcat(line, "\n");
}

static void logSample()
{
  char line[200];
  buildCsvLine(line, sizeof(line));
  logFile.print(line);
  if (++flushCnt >= 10) { flushCnt = 0; logFile.flush(); }
}

/* =====================================================================
 *  串口命令
 * ===================================================================== */
static void printHelp()
{
  Serial.println(F("\n===== PID 差速抑制 · 命令 ====="));
  Serial.println(F("  w 前进   s 后退   a 左转   d 右转   x 刹车   c 滑行"));
  Serial.printf (F("  0~9 目标=数字×15rpm(3→45)  + / - 目标±5rpm（当前 %.0f）\n"), targetRpm);
  Serial.println(F("  r60 设目标 | o 开环/闭环切换 | z 编码器清零"));
  Serial.printf (F("  kp%.2f ki%.2f kd%.2f ff%.2f  → 串口如 kp3.0 直接改\n"), kp, ki, kd, ff);
  Serial.println(F("  p 打印一帧   t 遥测开关   e 串口CSV输出   v8.06 电池电压   h 帮助"));
  Serial.println(F("研究建议：起步→'o'来回切换看 d(rpm)/gyrZ 变化；z→w→5s→x 得阶跃响应"));
}

static void setDir(int8_t dl, int8_t dr, const char *name)
{
  dirL = dl; dirR = dr;
  resetPid();
  if (dl == 0 && dr == 0) { brakeAll(); Serial.printf("-> %s（已刹车）\n", name); }
  else                    { Serial.printf("-> %s 目标 %.0frpm\n", name, targetRpm); }
}

static void handleChar(char c)
{
  if (c == '\r' || c == '\n') return;
  switch (c) {
    case 'w': setDir(+1, +1, "前进"); break;
    case 's': setDir(-1, -1, "后退"); break;
    case 'a': setDir(-1, +1, "原地左转"); break;
    case 'd': setDir(+1, -1, "原地右转"); break;
    case 'x': setDir(0, 0, "刹车"); break;
    case 'c': dirL = dirR = 0; setMotors(0, 0); resetPid(); Serial.println(F("-> 滑行断电")); break;
    case 'o': pidOn = !pidOn; resetPid();
              Serial.printf("-> %s模式\n", pidOn ? "PID 闭环" : "开环（同 PWM 对照）"); break;
    case 'z': encCountL = 0; encCountR = 0; lastCntL = 0; lastCntR = 0;
              Serial.println(F("-> 编码器已清零")); break;
    case 'p': printTelemetry(); break;
    case 'e': csvOut = !csvOut;       // e = export（原用 l，与数字 1 形近易误触，已改）
              if (csvOut) Serial.println(CSV_HEADER);
              Serial.printf("-> 串口 CSV 输出 %s（用电脑记录这些数据行）\n", csvOut ? "开" : "关");
              break;
    case 't': telemetryOn = !telemetryOn; Serial.printf("-> 遥测 %s\n", telemetryOn ? "开" : "关"); break;
    case 'h': printHelp(); break;
    default:
      if (c >= '0' && c <= '9') {
        targetRpm = (c - '0') * 15;
        Serial.printf("-> 目标 %.0f rpm\n", targetRpm);
      } else if (c == '+' || c == '=') {
        targetRpm = min(150.0f, targetRpm + 5); Serial.printf("-> 目标 %.0f rpm\n", targetRpm);
      } else if (c == '-' || c == '_') {
        targetRpm = max(0.0f, targetRpm - 5); Serial.printf("-> 目标 %.0f rpm\n", targetRpm);
      } else {
        Serial.printf("未知命令 '%c'（h 查看帮助）\n", c);
      }
      break;
  }
}

static void handleLine(char *line)
{
  struct { const char *cmd; float *val; float lo, hi; const char *name; } P[] = {
    { "kp", &kp, 0,  50, "Kp" },
    { "ki", &ki, 0,  10, "Ki" },
    { "kd", &kd, 0,  10, "Kd" },
    { "ff", &ff, 0,   3, "前馈" },
    { "r",  &targetRpm, 10, 150, "目标转速" },
  };
  for (auto &p : P) {
    size_t n = strlen(p.cmd);
    if (strncasecmp(line, p.cmd, n) == 0 && line[n] != '\0') {
      float v = atof(line + n);
      if (v >= p.lo && v <= p.hi) {
        *p.val = v;
        Serial.printf("-> %s = %.3f（目标 %.0frpm, kp%.2f ki%.2f kd%.2f ff%.2f）\n",
                      p.name, v, targetRpm, kp, ki, kd, ff);
      } else {
        Serial.printf("格式: %s数值（范围 %.0f~%.0f）\n", p.cmd, p.lo, p.hi);
      }
      return;
    }
  }
  if ((line[0] == 'v' || line[0] == 'V') && line[1] != '\0') {
    float v = atof(line + 1);
    if (v >= 5.0f && v <= 9.0f) { vBatFallback = v; Serial.printf("-> 电池电压替代值 = %.2fV\n", vBatFallback); }
    else Serial.println(F("格式: v8.06（5~9V）"));
    return;
  }
  for (char *q = line; *q; q++) handleChar(*q);
}

/* =====================================================================
 *  Setup / Loop
 * ===================================================================== */
static void i2cScan()
{
  Serial.print(F("I2C 扫描:"));
  uint8_t n = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      Serial.printf(" 0x%02X", a); n++;
      if (a == ADDR_INA) inaOK = true;
    }
  }
  if (n == 0) Serial.print(F(" （未发现器件）"));
  Serial.println();
}

void setup()
{
  Serial.begin(115200);
  delay(300);
  Serial.println(F("\n===== IPQ · 双电机差速 PID 抑制 ====="));

  pinMode(PIN_AIN1, OUTPUT);  digitalWrite(PIN_AIN1, LOW);
  pinMode(PIN_AIN2, OUTPUT);  digitalWrite(PIN_AIN2, LOW);
  pinMode(PIN_BIN1, OUTPUT);  digitalWrite(PIN_BIN1, LOW);
  pinMode(PIN_BIN2, OUTPUT);  digitalWrite(PIN_BIN2, LOW);
  pwmSetup(PIN_AIN2);
  pwmSetup(PIN_BIN2);
  pwmWrite(PIN_AIN2, 0);
  pwmWrite(PIN_BIN2, 0);

  pinMode(PIN_ENC_LA, INPUT);  pinMode(PIN_ENC_LB, INPUT);
  pinMode(PIN_ENC_RA, INPUT);  pinMode(PIN_ENC_RB, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_LA), isrEncL, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_RA), isrEncR, RISING);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setTimeout(50);
  i2cScan();
  if (inaOK) { inaOK = inaInit(); }
  if (!inaOK) inaRetryAt = millis() + 10000;

  imuOK = imuInit();
  if (imuOK) Serial.printf("  IMU: %s (0x%02X) 初始化成功\n", imuIsLSM ? "LSM6 系" : "MPU6050", imuAddr);
  else       Serial.println(F("  IMU: 未识别到（gyrZ 将不可用）"));
  if (imuOK) {                                 // 陀螺零偏校准：上电保持静止
    Serial.print(F("  IMU 陀螺零偏校准中（保持静止）…"));
    int16_t a[3], t, g[3];
    long acc[3] = {0, 0, 0};
    int n = 0;
    uint32_t t0 = millis();
    while (n < 200 && millis() - t0 < 1000) {
      if (imuRead(a, t, g)) { acc[0] += g[0]; acc[1] += g[1]; acc[2] += g[2]; n++; }
      delay(2);
    }
    if (n > 0) {
      gyroBias[0] = acc[0] / (float)n; gyroBias[1] = acc[1] / (float)n; gyroBias[2] = acc[2] / (float)n;
      Serial.printf("完成（Z 轴 %.1f dps）\n", gyroBias[2] * (imuIsLSM ? 8.75f / 1000 : 1.0f / 131.0f));
    } else Serial.println(F("失败"));
  }

  sdInit();
  printHelp();
  Serial.println(F("上电默认：PID 闭环、目标 45rpm、kp2.0 ki0.15 kd0 ff1.3"));
}

void loop()
{
  /* 行命令缓冲（同测试程序） */
  static char     lineBuf[16];
  static uint8_t  lineLen = 0;
  static uint32_t lastCharMs = 0;
  while (Serial.available()) {
    char c = (char)Serial.read();
    lastCharMs = millis();
    if (c == '\r' || c == '\n') {
      if (lineLen > 0) { lineBuf[lineLen] = 0; handleLine(lineBuf); lineLen = 0; }
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    }
  }
  if (lineLen > 0 && millis() - lastCharMs > 50) {
    lineBuf[lineLen] = 0; handleLine(lineBuf); lineLen = 0;
  }

  static uint32_t tCtrl = 0;
  uint32_t now = millis();
  if (now - tCtrl >= TSAMP_MS) {
    tCtrl = now;
    controlStep();
    if (telemetryOn) printTelemetry();
    if (sdOK)        logSample();
    if (csvOut)    { char line[200]; buildCsvLine(line, sizeof(line)); Serial.print(line); }
  }
}
