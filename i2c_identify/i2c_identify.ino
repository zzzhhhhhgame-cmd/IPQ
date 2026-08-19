/*
 * I2C 器件识别小程序
 * 用途：确认传感器板上实际装的是什么芯片（MPU6050 / QMI8658 / LSM6 系列...）
 * 用法：接线保持不变，选 ESP32 Dev Module 上传，串口监视器 115200，
 *       按 RST 可重新打印。把输出原样发回即可。
 */
#include <Wire.h>

bool readReg(uint8_t addr, uint8_t reg, uint8_t &out)
{
  Wire.beginTransmission(addr); Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((uint8_t)addr, (uint8_t)1) != 1) return false;
  out = Wire.read();
  return true;
}

void setup()
{
  Serial.begin(115200);
  delay(500);
  Wire.begin(21, 22);          // SDA=21, SCL=22，与主程序一致

  Serial.println(F("\n===== I2C 器件识别 ====="));
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() != 0) continue;   // 无应答，跳过
    Serial.printf("发现器件: 0x%02X\n", a);
    uint8_t v;
    // 不同系列的 WHO_AM_I(身份) 寄存器位置不同，全部读一遍：
    if (readReg(a, 0x0F, v))
      Serial.printf("  寄存器 0x0F (ST LSM6/L3G 系列身份位) = 0x%02X\n", v);
    if (readReg(a, 0x00, v))
      Serial.printf("  寄存器 0x00 (QMI8658 身份位)         = 0x%02X\n", v);
    if (readReg(a, 0x75, v))
      Serial.printf("  寄存器 0x75 (InvenSense MPU 系列身份位) = 0x%02X\n", v);
  }
  Serial.println(F("识别完成，请把以上输出发回。"));
}

void loop() {}
