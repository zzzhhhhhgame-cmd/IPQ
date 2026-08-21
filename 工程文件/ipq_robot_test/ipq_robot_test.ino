/*
 * =====================================================================
 *  IPQ 移动机器人 · 全系统联合测试程序
 * =====================================================================
 *  硬件：ESP32 DevKit V1 + DRV8833 + JGB37-520B(带编码器)×2
 *        + INA226 + IMU(MPU6050 或 LSM6DS3，程序自动识别) + microSD(SPI 模块)
 *
 *  引脚与 wiring-checklist.html v3.1 逐线对应：
 *    电机驱动  GPIO23→AIN1(左方向)   GPIO19→AIN2(左PWM)
 *              GPIO18→BIN1(右方向)   GPIO16→BIN2(右PWM)   STBY 已接 3.3V
 *    编码器    左 A→GPIO34  左 B→GPIO35
 *              右 A→GPIO32  右 B→GPIO33（v3.3 改，普通脚；左侧两脚仍 input-only）
 *    I²C       GPIO21=SDA   GPIO22=SCL     （INA226=0x40；IMU 自动识别：
 *              MPU6050=0x68/0x69 或 LSM6DS3=0x6A/0x6B）
 *    SPI(SD)   SCK=GPIO14   MOSI=GPIO15    MISO=GPIO2   CS=GPIO27（v3.2 改）
 *
 *  需要安装的库：无。只使用 ESP32 Arduino 核心自带的 Wire / SPI / SD。
 *  前提：Arduino IDE 已装 "esp32 by Espressif Systems" 开发板支持(≥2.0.2)，
 *        开发板选 "ESP32 Dev Module"，串口监视器波特率 115200。
 *        ⚠ 烧录失败时先拔掉 microSD 模块（GPIO2 是启动脚）。
 * =====================================================================
 */

#include <Wire.h>
#include <SPI.h>
#include <SD.h>

/* ---------------- 引脚定义（与接线清单一一对应） ---------------- */
static const uint8_t PIN_AIN1    = 23;   // 左电机 方向
static const uint8_t PIN_AIN2    = 19;   // 左电机 PWM
static const uint8_t PIN_BIN1    = 18;   // 右电机 方向
static const uint8_t PIN_BIN2    = 16;   // 右电机 PWM
static const uint8_t PIN_ENC_LA  = 34;   // 左编码器 A 相（input-only）
static const uint8_t PIN_ENC_LB  = 35;   // 左编码器 B 相（input-only）
static const uint8_t PIN_ENC_RA  = 32;   // 右编码器 A 相（v3.3：由 36 改 32）
static const uint8_t PIN_ENC_RB  = 33;   // 右编码器 B 相（v3.3：由 39 改 33）
static const uint8_t PIN_SDA     = 21;
static const uint8_t PIN_SCL     = 22;
static const uint8_t PIN_SD_SCK  = 14;
static const uint8_t PIN_SD_MOSI = 15;
static const uint8_t PIN_SD_MISO = 2;
static const uint8_t PIN_SD_CS   = 27;   // v3.2：片选由 GPIO13 改到 GPIO27

/* ---------------- I²C 器件地址 ---------------- */
static const uint8_t ADDR_INA = 0x40;    // INA226（AD0 类跳线默认 0x40）

/* ---------------- 可按实际情况修改的参数 ---------------- */
#define PWM_FREQ_HZ   20000   // DRV8833 支持 0~250kHz；20kHz 无啸叫
#define TELE_MS       100     // 遥测/记录周期 100ms（10Hz）
#define R_SHUNT       0.1f    // INA226 采样电阻：板上丝印 R100=0.1Ω(常见)
static float vBatFallback = 8.0f;  // 模块母线通道坏时的替代电池电压(V)；串口发 "v8.06" 随时更新
                              //   R010=0.01Ω、R001=0.001Ω；0.1Ω 时量程约 ±0.8A
#define ENC_PPR       11      // JGB37-520B 编码器 11 PPR（A 相上升沿计数）
#define GEAR_RATIO    30      // 减速比 1:30（BOM 确认，333rpm 档）
#define ENC_L_INVERT  0       // 前进时左编码器计数变负 → 改成 1
#define ENC_R_INVERT  0       // 前进时右编码器计数变负 → 改成 1
#define MOT_L_INVERT  0       // 'w' 前进时左轮实际反转 → 改成 1
#define MOT_R_INVERT  0       // 'w' 前进时右轮实际反转 → 改成 1

/* =====================================================================
 *  LEDC PWM 封装：ESP32 Arduino 核心 2.x 与 3.x 的 LEDC API 不同，
 *  这里各写一份，保证两种核心都能编译。
 * ===================================================================== */
#if defined(ESP_ARDUINO_VERSION) && ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
static void pwmSetup(uint8_t pin)
{
  ledcAttach(pin, PWM_FREQ_HZ, 8);            // 3.x：直接把引脚挂到 8 位 LEDC
}
static void pwmWrite(uint8_t pin, uint32_t duty)
{
  ledcWrite(pin, duty);
}
#else
static uint8_t pwmChOf(uint8_t pin) { return (pin == PIN_AIN2) ? 0 : 1; }
static void pwmSetup(uint8_t pin)
{
  ledcSetup(pwmChOf(pin), PWM_FREQ_HZ, 8);    // 2.x：先建通道再绑引脚
  ledcAttachPin(pin, pwmChOf(pin));
}
static void pwmWrite(uint8_t pin, uint32_t duty)
{
  ledcWrite(pwmChOf(pin), duty);
}
#endif

/* =====================================================================
 *  DRV8833 电机控制
 *  接线方案：IN1=方向(数字)、IN2=PWM。真值表：
 *    IN1=1, IN2=0 正转 | IN1=0, IN2=1 反转 | IN1=IN2 刹车/滑行
 *  本函数保证：speed 的绝对值在正反两个方向上对应相同的占空比。
 * ===================================================================== */
static void motorWrite(uint8_t dirPin, uint8_t pwmPin, int speed)
{
  if (speed > 0) {                 // IN2 低电平期间正转 → PWM 值取反
    digitalWrite(dirPin, HIGH);
    pwmWrite(pwmPin, 255 - speed);
  } else if (speed < 0) {          // IN2 高电平期间反转
    digitalWrite(dirPin, LOW);
    pwmWrite(pwmPin, (uint32_t)(-speed));
  } else {                         // 0 = 滑行（输出高阻，电机断电）
    digitalWrite(dirPin, LOW);
    pwmWrite(pwmPin, 0);
  }
}

static void setMotors(int l, int r)          // l,r ∈ [-255,255]
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

static void brakeAll()                       // 两个电机能耗刹车
{
  digitalWrite(PIN_AIN1, HIGH); pwmWrite(PIN_AIN2, 255);
  digitalWrite(PIN_BIN1, HIGH); pwmWrite(PIN_BIN2, 255);
}

/* ---------------- 运动状态 ---------------- */
static int8_t  dirL = 0, dirR = 0;   // 最近一次方向指令：-1/0/+1
static int     speedPct = 30;        // 目标速度 0~100%（上电默认 30% 低速）
static float   trimL = 1.0f, trimR = 1.0f;   // 左/右轮 PWM 微调，校正差速（tl1.05 / tr0.94）

static void applyDrive()
{
  if (dirL == 0 && dirR == 0) return;
  int dl = constrain((int)(speedPct * 255 / 100 * trimL + 0.5f), 0, 255);
  int dr = constrain((int)(speedPct * 255 / 100 * trimR + 0.5f), 0, 255);
  setMotors(dirL * dl, dirR * dr);
}

/* =====================================================================
 *  编码器（GPIO34/35/36/39，input-only，无内部上拉；
 *         JGB37 编码器板自带输出，直接计数即可）
 * ===================================================================== */
static volatile int32_t encCountL = 0;
static volatile int32_t encCountR = 0;

void IRAM_ATTR isrEncL() { digitalRead(PIN_ENC_LB) ? encCountL++ : encCountL--; }
void IRAM_ATTR isrEncR() { digitalRead(PIN_ENC_RB) ? encCountR++ : encCountR--; }

/* =====================================================================
 *  I²C 通用寄存器读写（INA226 / MPU6050 都是标准 I²C 寄存器件）
 * ===================================================================== */
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

static int16_t i2cRead16(uint8_t addr, uint8_t reg, bool &ok)   // 返回有符号 16 位
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

/* =====================================================================
 *  INA226 电流/电压/功率（地址 0x40）
 *    0x00 CONFIG   0x01 分流电压(2.5µV/LSB)   0x02 母线电压(1.25mV/LSB)
 *  电流不用校准寄存器，直接 I = V_分流 / R_采样 计算。
 * ===================================================================== */
static bool inaOK = false;
static uint32_t inaRetryAt = 0;      // INA226 掉线后的自动重试时刻（0=不重试）

static bool inaInit()
{
  // CONFIG: 平均 16 次 ×(1.1ms+1.1ms)，分流+母线连续测量 ≈35ms 出一个新值
  bool ok = i2cWrite16(ADDR_INA, 0x00, 0x4587);
  // 诊断：回读配置 + 厂商/芯片 ID（正品 INA226：0xFE=0x5449"TI"，0xFF=0x2260）
  bool okR;
  uint16_t cfg = (uint16_t)i2cRead16(ADDR_INA, 0x00, okR);
  uint16_t mfr = (uint16_t)i2cRead16(ADDR_INA, 0xFE, okR);
  uint16_t die = (uint16_t)i2cRead16(ADDR_INA, 0xFF, okR);
  Serial.printf("  [INA诊断] CFG回读=0x%04X  MFR_ID(0xFE)=0x%04X  DIE_ID(0xFF)=0x%04X\n", cfg, mfr, die);
  if (mfr == 0x5449 && die == 0x2260)
    Serial.println(F("    → 正品 INA226；若 bat 仍为 0.00V，重点查 INA226 的 GND 线（清单线21，到蓝轨）"));
  else
    Serial.println(F("    → 非 INA226 标准身份（兼容片？），电流仍按现状可用；把此行发回，按实际芯片修电压换算"));
  return ok;
}

/* =====================================================================
 *  IMU：自动识别两种芯片（实测本板为 LSM6DS3，地址 0x6B）
 *    MPU6050：地址 0x68/0x69，大端数据，±2g=16384 LSB/g，±250°/s=131 LSB/(°/s)
 *    LSM6DS3：地址 0x6A/0x6B，小端数据，±2g=0.061 mg/LSB，±245°/s=8.75 mdps/LSB
 * ===================================================================== */
static bool    imuOK    = false;
static bool    imuIsLSM = false;    // true=LSM6DS3，false=MPU6050
static uint8_t imuAddr  = 0;
static float   gyroBias[3] = {0, 0, 0};  // 开机静止校准的陀螺零偏（原始 LSB）

static bool imuRead(int16_t a[3], int16_t &tRaw, int16_t g[3]);   // 前置声明

static bool imuInit()
{
  uint8_t v;
  // LSM6 系列：WHO_AM_I=0x0F，DS3/DSL/TR-C=0x6A，DSR=0x6B，DSO=0x6C（寄存器布局兼容）
  for (uint8_t a = 0x6A; a <= 0x6B; a++) {
    if (!i2cRead8(a, 0x0F, v)) continue;
    Serial.printf("  [IMU诊断] 0x%02X: WHO_AM_I(0x0F)=0x%02X", a, v);
    if (v == 0x6A || v == 0x6B || v == 0x6C) {
      Serial.println(F(" → 按 LSM6 系列初始化"));
      imuAddr = a; imuIsLSM = true;
      bool ok = i2cWrite8(a, 0x12, 0x44);   // CTRL3_C：BDU=1 防止高低字节撕裂
      ok &= i2cWrite8(a, 0x10, 0x40);       // CTRL1_XL：加速度 104Hz、±2g
      ok &= i2cWrite8(a, 0x11, 0x40);       // CTRL2_G： 陀螺 104Hz、±245°/s
      delay(50);
      return ok;
    }
    Serial.println();
  }
  // MPU6050：WHO_AM_I=0x75，应答 0x68
  for (uint8_t a = 0x68; a <= 0x69; a++) {
    if (!i2cRead8(a, 0x75, v) || v != 0x68) continue;
    Serial.printf("  [IMU诊断] 0x%02X: WHO_AM_I(0x75)=0x68 → 按 MPU6050 初始化\n", a);
    imuAddr = a; imuIsLSM = false;
    bool ok = i2cWrite8(a, 0x6B, 0x01);     // 唤醒，时钟=PLL(X 轴陀螺)
    ok &= i2cWrite8(a, 0x19, 0x04);         // 采样率 1kHz/(1+4)=200Hz
    ok &= i2cWrite8(a, 0x1A, 0x03);         // DLPF 44Hz 低通
    ok &= i2cWrite8(a, 0x1B, 0x00);         // 陀螺 ±250°/s
    ok &= i2cWrite8(a, 0x1C, 0x00);         // 加速度 ±2g
    delay(50);
    return ok;
  }
  // 身份码都未匹配（如本板 WHO_AM_I=0x69）：按 LSM6 寄存器盲试探——
  // 写 CTRL3_C 后回读，能对上说明寄存器语义兼容（兼容/克隆芯片常见）
  for (uint8_t a = 0x6A; a <= 0x6B; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() != 0) continue;          // 该地址无器件
    if (!i2cWrite8(a, 0x12, 0x44)) continue;            // CTRL3_C：BDU=1、地址自增
    uint8_t rb = 0;
    if (!i2cRead8(a, 0x12, rb) || rb != 0x44) continue; // 回读不符 → 不是 LSM6 兼容芯片
    i2cWrite8(a, 0x10, 0x40);                           // CTRL1_XL：104Hz、±2g
    i2cWrite8(a, 0x11, 0x40);                           // CTRL2_G：104Hz、±245°/s
    delay(60);
    imuAddr = a; imuIsLSM = true;
    int16_t ra[3], rt, rg[3];
    if (imuRead(ra, rt, rg)) {
      float ax = ra[0] * 0.061f / 1000, ay = ra[1] * 0.061f / 1000, az = ra[2] * 0.061f / 1000;
      float m  = sqrtf(ax * ax + ay * ay + az * az);
      Serial.printf("  [IMU诊断] 0x%02X 按 LSM6 寄存器试探成功(CTRL回读一致)，静止合加速度 %.2f g", a, m);
      if (m > 0.4f && m < 1.6f) Serial.println(F(" ≈1g → 按兼容芯片启用"));
      else                      Serial.println(F("（不在1g附近——请将板静止放置；已启用，注意核对遥测数值）"));
      return true;
    }
  }
  // 都没匹配：打印候选芯片身份寄存器的原始值，据此人工识别
  Serial.println(F("  [IMU诊断] 未匹配已知芯片，原始身份值："));
  for (uint8_t a = 0x68; a <= 0x6B; a++) {
    Serial.printf("    0x%02X:", a);
    if (i2cRead8(a, 0x00, v)) Serial.printf(" reg0x00=0x%02X", v);
    if (i2cRead8(a, 0x0F, v)) Serial.printf(" reg0x0F=0x%02X", v);
    if (i2cRead8(a, 0x75, v)) Serial.printf(" reg0x75=0x%02X", v);
    Serial.println();
  }
  return false;
}

static bool imuRead(int16_t a[3], int16_t &tRaw, int16_t g[3])
{
  Wire.beginTransmission(imuAddr);
  if (imuIsLSM) Wire.write(0x22);           // LSM：0x22 起 12 字节=陀螺xyz+加速度xyz
  else          Wire.write(0x3B);           // MPU：0x3B 起 14 字节=加速度+温度+陀螺
  if (Wire.endTransmission(false) != 0) return false;
  uint8_t n = imuIsLSM ? 12 : 14;
  if (Wire.requestFrom((uint8_t)imuAddr, n) != n) return false;
  if (imuIsLSM) {
    for (int i = 0; i < 3; i++)             // LSM 小端：低字节在前
      g[i] = (int16_t)((uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8));
    for (int i = 0; i < 3; i++)
      a[i] = (int16_t)((uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8));
    Wire.beginTransmission(imuAddr); Wire.write(0x20);   // 温度单独读
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom((uint8_t)imuAddr, (uint8_t)2) != 2) return false;
    uint8_t lo = Wire.read(), hi = Wire.read();
    tRaw = (int16_t)((uint16_t)lo | ((uint16_t)hi << 8));
  } else {
    for (int i = 0; i < 3; i++)             // MPU 大端：高字节在前
      a[i] = ((int16_t)Wire.read() << 8) | Wire.read();
    tRaw = ((int16_t)Wire.read() << 8) | Wire.read();
    for (int i = 0; i < 3; i++)
      g[i] = ((int16_t)Wire.read() << 8) | Wire.read();
  }
  return true;
}

/* =====================================================================
 *  microSD（SPI：SCK=14 MOSI=15 MISO=2 CS=13）
 *  每个遥测周期追加一行 CSV，每 10 行落盘一次。
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
  for (int i = 0; i < 1000; i++) {            // 自动找空文件名，避免覆盖旧数据
    snprintf(name, sizeof(name), "/ipq%03d.csv", i);
    if (!SD.exists(name)) break;
  }
  logFile = SD.open(name, FILE_WRITE);
  if (!logFile) { Serial.println(F("SD 卡无法创建日志文件")); return; }
  logFile.println(F("ms,encL,encR,dEncL,dEncR,rpmL,rpmR,busV,curA,powW,"
                    "ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,mpuTempC"));
  logFile.flush();
  sdOK = true;
  Serial.printf("SD: 日志写入 %s\n", name);
}

/* =====================================================================
 *  采样与输出
 * ===================================================================== */
struct Sample {
  uint32_t ms;
  int32_t  eL, eR, dL, dR;
  float    rpmL, rpmR;
  float    vBus, iMot, pMot;                  // 缺器件时为 NAN
  bool     vAssumed;                          // bat 为替代值(模块母线通道坏)时为真
  float    ax, ay, az, gx, gy, gz, temp;
};
static Sample s;
static int32_t lastL = 0, lastR = 0;
static bool    telemetryOn = true;

static void collectSample()
{
  s.ms = millis();
  static uint32_t tPrev = 0;                  // 按实际间隔算转速，遥测暂停后第一帧不出假峰值
  uint32_t dt = s.ms - tPrev;
  if (dt == 0) dt = 1;
  tPrev = s.ms;

  int32_t l = encCountL, r = encCountR;       // 32 位对齐读取，原子操作
  s.eL = l;  s.eR = r;
  s.dL = l - lastL;  s.dR = r - lastR;
  lastL = l;         lastR = r;
  const float k = 60000.0f / dt / (ENC_PPR * GEAR_RATIO);
  s.rpmL = s.dL * k * (ENC_L_INVERT ? -1.0f : 1.0f);
  s.rpmR = s.dR * k * (ENC_R_INVERT ? -1.0f : 1.0f);

  if (!inaOK && inaRetryAt && (int32_t)(millis() - inaRetryAt) >= 0) {
    inaRetryAt = 0;
    if (i2cWrite16(ADDR_INA, 0x00, 0x4587)) {  // 轻量重连：只重写配置
      inaOK = true;
      Serial.println(F("!! INA226 已重新上线"));
    } else {
      inaRetryAt = millis() + 10000;           // 仍不在线，10s 后再试
    }
  }
  if (inaOK) {                                 // INA226：先分流电压→电流，再母线电压→功率
    bool ok;
    int16_t shunt = i2cRead16(ADDR_INA, 0x01, ok);
    if (!ok) { inaOK = false; inaRetryAt = millis() + 10000; Serial.println(F("!! INA226 掉线，10s 后自动重试（查它的 4 根线是否被震松）")); }
    else     { s.iMot = (shunt * 2.5e-6f) / R_SHUNT; }
    int16_t bus = i2cRead16(ADDR_INA, 0x02, ok);
    if (!ok) { inaOK = false; }
    else {
      s.vBus = bus * 0.00125f;
      s.vAssumed = (s.vBus < 0.5f);          // 读不到母线 → 用替代电压估算功率
      if (s.vAssumed) s.vBus = vBatFallback;
      s.pMot = s.vBus * s.iMot;
    }
  }
  if (!inaOK) { s.vBus = s.iMot = s.pMot = NAN; }

  int16_t ra[3], rt, rg[3];
  if (imuOK && imuRead(ra, rt, rg)) {
    if (imuIsLSM) {
      s.ax = ra[0] * 0.061f / 1000;  s.ay = ra[1] * 0.061f / 1000;  s.az = ra[2] * 0.061f / 1000;
      s.gx = (rg[0]-gyroBias[0]) * 8.75f / 1000;   s.gy = (rg[1]-gyroBias[1]) * 8.75f / 1000;   s.gz = (rg[2]-gyroBias[2]) * 8.75f / 1000;
      s.temp = rt / 256.0f + 25.0f;
    } else {
      s.ax = ra[0] / 16384.0f;  s.ay = ra[1] / 16384.0f;  s.az = ra[2] / 16384.0f;
      s.gx = (rg[0]-gyroBias[0]) / 131.0f;    s.gy = (rg[1]-gyroBias[1]) / 131.0f;    s.gz = (rg[2]-gyroBias[2]) / 131.0f;
      s.temp = rt / 340.0f + 36.53f;
    }
  } else {
    if (imuOK) Serial.println(F("!! IMU 读取失败"));
    imuOK = false;
    s.ax = s.ay = s.az = s.gx = s.gy = s.gz = s.temp = NAN;
  }
}

static void printSample()
{
  Serial.printf("[%6.1fs] encL %+6ld (%+4ld)  encR %+6ld (%+4ld)  rpm L %+6.1f R %+6.1f | ",
                s.ms / 1000.0, (long)s.eL, (long)s.dL, (long)s.eR, (long)s.dR,
                s.rpmL, s.rpmR);
  if (!isnan(s.vBus))
    Serial.printf("bat %.2f%sV  cur %.3fA  pow %.2fW | ", s.vBus, s.vAssumed ? "*" : "", s.iMot, s.pMot);
  else
    Serial.print(F("bat  ----   cur  ----   pow  ---- | "));
  if (!isnan(s.ax))
    Serial.printf("acc %+.2f %+.2f %+.2f g  gyr %+5.1f %+5.1f %+5.1f dps  %.1fC\n",
                  s.ax, s.ay, s.az, s.gx, s.gy, s.gz, s.temp);
  else
    Serial.println(F("IMU 无数据"));
}

/* ---- CSV 追加：NaN 写成空字段，方便后续 Excel/Python 处理 ---- */
static void appI(char *line, long v)   { char c[20]; snprintf(c, sizeof(c), ",%ld", v); strcat(line, c); }
static void appF(char *line, float v)
{
  char c[24];
  if (isnan(v)) strcat(line, ",");
  else { snprintf(c, sizeof(c), ",%.4f", v); strcat(line, c); }
}

static void logSample()
{
  char line[256] = "";
  char head[24];
  snprintf(head, sizeof(head), "%lu", (unsigned long)s.ms);
  strcat(line, head);
  appI(line, s.eL);  appI(line, s.eR);  appI(line, s.dL);  appI(line, s.dR);
  appF(line, s.rpmL); appF(line, s.rpmR);
  appF(line, s.vBus); appF(line, s.iMot); appF(line, s.pMot);
  appF(line, s.ax);  appF(line, s.ay);  appF(line, s.az);
  appF(line, s.gx);  appF(line, s.gy);  appF(line, s.gz);
  appF(line, s.temp);
  strcat(line, "\n");
  logFile.print(line);
  if (++flushCnt >= 10) { flushCnt = 0; logFile.flush(); }   // 每 1s 落盘
}

/* =====================================================================
 *  演示动作序列（'g' 触发，非阻塞）：前进 2s → 刹车 0.8s → 后退 2s → 刹车
 * ===================================================================== */
struct DemoStep { int8_t l, r; uint32_t ms; };
static const DemoStep DEMO_STEPS[] = { {+1, +1, 2000}, {0, 0, 800}, {-1, -1, 2000} };
static const uint8_t DEMO_N = sizeof(DEMO_STEPS) / sizeof(DEMO_STEPS[0]);
static bool     demoOn  = false;
static uint8_t  demoIdx = 0;
static uint32_t demoT0  = 0;

static void demoApply()
{
  dirL = DEMO_STEPS[demoIdx].l;
  dirR = DEMO_STEPS[demoIdx].r;
  if (dirL == 0 && dirR == 0) brakeAll();
  else                        applyDrive();
}

static void runDemo()
{
  if (!demoOn) return;
  if (millis() - demoT0 >= DEMO_STEPS[demoIdx].ms) {
    demoT0 += DEMO_STEPS[demoIdx].ms;
    if (++demoIdx >= DEMO_N) {
      demoOn = false; dirL = dirR = 0; brakeAll();
      Serial.println(F("== 演示序列完成，已刹车 =="));
    } else {
      demoApply();
    }
  }
}

/* =====================================================================
 *  串口命令
 * ===================================================================== */
static void printHelp()
{
  Serial.println(F("\n===== 命令（串口发送单个字符）====="));
  Serial.println(F("  w 前进    s 后退    a 原地左转    d 原地右转"));
  Serial.println(F("  x 刹车    c 滑行断电"));
  Serial.println(F("  + 速度+10%    - 速度-10%    0~9 直接设定 0%~90%"));
  Serial.println(F("  g 演示：前进2s→刹车→后退2s→刹车"));
  Serial.println(F("  z 编码器计数清零    p 立即打印一帧    t 开/关周期遥测    h 帮助"));
  Serial.println(F("  v8.06 设置电池电压替代值（功率按它算；换新模块后自动用实测）"));
  Serial.println(F("  tl1.05 / tr0.94 左/右轮 PWM 微调(校正差速)；单独的 t 仍是遥测开关"));
  Serial.printf ("  当前速度：%d%%\n", speedPct);
}

static void handleChar(char c)
{
  if (c == '\r' || c == '\n') return;
  switch (c) {
    case 'w': demoOn = false; dirL = +1; dirR = +1; applyDrive(); Serial.printf("-> 前进 %d%%\n", speedPct); break;
    case 's': demoOn = false; dirL = -1; dirR = -1; applyDrive(); Serial.printf("-> 后退 %d%%\n", speedPct); break;
    case 'a': demoOn = false; dirL = -1; dirR = +1; applyDrive(); Serial.printf("-> 原地左转 %d%%\n", speedPct); break;
    case 'd': demoOn = false; dirL = +1; dirR = -1; applyDrive(); Serial.printf("-> 原地右转 %d%%\n", speedPct); break;
    case 'x': demoOn = false; dirL = dirR = 0; brakeAll();      Serial.println(F("-> 刹车")); break;
    case 'c': demoOn = false; dirL = dirR = 0; setMotors(0, 0); Serial.println(F("-> 滑行断电")); break;
    case '+': case '=':
      speedPct = min(100, speedPct + 10); applyDrive();
      Serial.printf("-> 速度 %d%%\n", speedPct); break;
    case '-': case '_':
      speedPct = max(0, speedPct - 10); applyDrive();
      Serial.printf("-> 速度 %d%%\n", speedPct); break;
    case 'g':
      demoOn = true; demoIdx = 0; demoT0 = millis(); demoApply();
      Serial.println(F("-> 演示序列开始")); break;
    case 'z':
      encCountL = 0; encCountR = 0; lastL = 0; lastR = 0;
      Serial.println(F("-> 编码器计数已清零")); break;
    case 'p': {
      int32_t bl = lastL, br = lastR;         // 手动打印不占用周期遥测的增量基线
      collectSample();
      lastL = bl;  lastR = br;
      printSample();
      break;
    }
    case 't': telemetryOn = !telemetryOn;
      Serial.printf("-> 周期遥测 %s\n", telemetryOn ? "开" : "关"); break;
    case 'h': printHelp(); break;
    default:  Serial.printf("未知命令 '%c'（h 查看帮助）\n", c); break;
  }
}

/* ---- 行命令：v8.06 → 设置电池电压替代值；其余整行拆成单字符命令 ---- */
static void handleLine(char *line)
{
  if ((line[0] == 't' || line[0] == 'T') &&
      (line[1] == 'l' || line[1] == 'L' || line[1] == 'r' || line[1] == 'R') && line[2] != '\0') {
    float f = atof(line + 2);                   // tl1.05 / tr0.94 → 左/右轮 PWM 微调
    if (f >= 0.80f && f <= 1.20f) {
      if (line[1] == 'l' || line[1] == 'L') trimL = f; else trimR = f;
      applyDrive();
      Serial.printf("-> 轮速微调 L=%.2f R=%.2f\n", trimL, trimR);
    } else {
      Serial.println(F("格式: tl1.05 / tr0.94（范围 0.80~1.20）"));
    }
    return;
  }
  if ((line[0] == 'v' || line[0] == 'V') && line[1] != '\0') {
    float v = atof(line + 1);
    if (v >= 5.0f && v <= 9.0f) {
      vBatFallback = v;
      Serial.printf("-> 电池电压替代值 = %.2fV\n", vBatFallback);
    } else {
      Serial.println(F("格式: v8.06（范围 5~9V）"));
    }
    return;
  }
  for (char *p = line; *p; p++) handleChar(*p);
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
  if (n == 0) Serial.print(F(" （未发现器件，请检查 21/22 接线）"));
  Serial.println();
}

void setup()
{
  Serial.begin(115200);
  delay(300);
  Serial.println(F("\n===== IPQ 机器人全系统测试 ====="));

  /* 电机：先全部拉低（滑行，最安全），再初始化 PWM */
  pinMode(PIN_AIN1, OUTPUT);  digitalWrite(PIN_AIN1, LOW);
  pinMode(PIN_AIN2, OUTPUT);  digitalWrite(PIN_AIN2, LOW);
  pinMode(PIN_BIN1, OUTPUT);  digitalWrite(PIN_BIN1, LOW);
  pinMode(PIN_BIN2, OUTPUT);  digitalWrite(PIN_BIN2, LOW);
  pwmSetup(PIN_AIN2);                       // PWM 20kHz（DRV8833 支持，人耳无啸叫）
  pwmSetup(PIN_BIN2);
  pwmWrite(PIN_AIN2, 0);
  pwmWrite(PIN_BIN2, 0);

  /* 编码器中断（34/35/36/39 无内部上拉，JGB37 编码器板推挽输出可直接接） */
  pinMode(PIN_ENC_LA, INPUT);  pinMode(PIN_ENC_LB, INPUT);
  pinMode(PIN_ENC_RA, INPUT);  pinMode(PIN_ENC_RB, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_LA), isrEncL, RISING);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_RA), isrEncR, RISING);

  /* I2C 总线 + 器件识别（对应清单"上电快检"：应看到 0x40 和 0x68） */
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setTimeout(50);
  i2cScan();
  Serial.printf("  INA226 (0x40): %s\n", inaOK ? "在线" : "缺失!");
  if (inaOK) { inaOK = inaInit(); Serial.printf("  INA226 配置: %s\n", inaOK ? "成功(16次平均)" : "失败"); }
  if (!inaOK) inaRetryAt = millis() + 10000;   // 启动时缺失也周期重试（支持热插拔）
  imuOK = imuInit();
  if (imuOK) Serial.printf("  IMU: %s (0x%02X) 初始化成功\n", imuIsLSM ? "LSM6 系" : "MPU6050", imuAddr);
  else       Serial.println(F("  IMU: 未识别到（支持 MPU6050 / LSM6 系列）"));
  if (imuOK) {                                 // 陀螺零偏校准：上电时保持小车静止
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
      float k = imuIsLSM ? 8.75f / 1000 : 1.0f / 131.0f;
      Serial.printf("完成，零偏 %.1f %.1f %.1f dps\n", gyroBias[0]*k, gyroBias[1]*k, gyroBias[2]*k);
    } else {
      Serial.println(F("失败（读取异常）"));
    }
  }

  /* microSD */
  sdInit();

  Serial.printf("编码器: %d 脉冲/圈 × 1:%d = 每圈轮轴 %.0f 个计数(A相上升沿)\n",
                ENC_PPR, GEAR_RATIO, (float)(ENC_PPR * GEAR_RATIO));
  printHelp();
  Serial.println(F("上电默认电机为滑行断电状态，发 'g' 或 'w' 开始测试。"));
}

void loop()
{
  /* 行缓冲：支持 "v8.06" 带参数命令；串口监视器没配行结束符时，50ms 静默也触发执行 */
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
  runDemo();

  static uint32_t tTele = 0;
  uint32_t now = millis();
  if (now - tTele >= TELE_MS) {
    tTele = now;
    collectSample();
    if (telemetryOn) printSample();
    if (sdOK)        logSample();
  }
}
