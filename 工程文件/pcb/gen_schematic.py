# -*- coding: utf-8 -*-
"""
gen_schematic.py — IPQ 载板原理图（SVG，风格与仓库文档一致）
输出: out/schematic.svg
"""
import os

W, H = 1500, 1060
BG, PANEL, BORDER = '#0d1117', '#161b22', '#2a3441'
TXT, DIM = '#e6edf3', '#8b98a9'
C_PWR, C_GND, C_SIG, C_I2C, C_SPI, C_ENC, C_MOT = '#ff8c42', '#f8516a', '#3fb950', '#d29922', '#f85149', '#bc8cff', '#58a6ff'

out = []
def A(s): out.append(s)
def L(x1,y1,x2,y2,c,w=2,dash=None):
    d = ' stroke-dasharray="%s"'%dash if dash else ''
    A('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%d"%s stroke-linecap="round"/>'%(x1,y1,x2,y2,c,w,d))
def R(x,y,w,h,rx=8,fill=PANEL,stroke=BORDER):
    A('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d" fill="%s" stroke="%s" stroke-width="1.5"/>'%(x,y,w,h,rx,fill,stroke))
def T(x,y,s,size=13,c=TXT,anchor='start',weight='normal'):
    A('<text x="%.1f" y="%.1f" font-family="-apple-system,PingFang SC,Helvetica" font-size="%d" fill="%s" text-anchor="%s" font-weight="%s">%s</text>'%(x,y,size,c,anchor,weight,s))

def box(x,y,w,h,title,sub,pins):
    """pins: list of (key, 显示文本, 颜色)。返回 {key:(x,y)} 左右两侧都有焊点。"""
    R(x,y,w,h)
    T(x+w/2, y+24, title, 15, TXT, 'middle', '600')
    if sub: T(x+w/2, y+41, sub, 10.5, DIM, 'middle')
    y0, dy, an = y+60, 21, {}
    for i,(key,lbl,col) in enumerate(pins):
        py = y0+i*dy
        A('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>'%(x,py,col))
        A('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>'%(x+w,py,col))
        T(x+9, py+4, lbl, 11.5, col)
        T(x+w-9, py+4, lbl, 11.5, col, 'end')
        an[key]=(x,py); an[key+'R']=(x+w,py)
    return an

A('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'%(W,H,W,H))
A('<rect width="%d" height="%d" fill="%s"/>'%(W,H,BG))
T(40,46,'IPQ-2026 小车模块载板 · 电路原理图',22,TXT,'start','600')
T(40,68,'Carrier v1.0 · 95×80mm 双层板 · 网表与 wiring v3.3 / 固件 ipq_robot_test 完全一致 · 2026-08-21',12,DIM)

# ---------------- 模块 ----------------
esp = box(590,100,300,545,'ESP32 DevKit V1 (30P)','插座 J1 · USB 朝板边',[
 ('3V3','3V3',C_PWR),('GND','GND',C_GND),('VIN','VIN ←5V',C_PWR),
 ('AIN1','D23→AIN1',C_SIG),('AIN2','D19→AIN2',C_SIG),
 ('BIN1','D18→BIN1',C_SIG),('BIN2','D16→BIN2',C_SIG),
 ('ELA','D34←左A',C_ENC),('ELB','D35←左B',C_ENC),
 ('ERA','D32←右A',C_ENC),('ERB','D33←右B',C_ENC),
 ('SDA','D21 SDA',C_I2C),('SCL','D22 SCL',C_I2C),
 ('CS','D27 CS',C_SPI),('SCK','D14 SCK',C_SPI),
 ('MOSI','D15 MOSI',C_SPI),('MISO','D2 MISO',C_SPI)])

drv = box(1060,100,330,345,'DRV8833 (D2-1-2F)','插座 J12 · 模块丝印朝上',[
 ('VM','VM',C_PWR),('GND','GND',C_GND),('STBY','STBY←3V3',C_PWR),
 ('AIN1','AIN1',C_SIG),('AIN2','AIN2',C_SIG),
 ('BIN1','BIN1',C_SIG),('BIN2','BIN2',C_SIG),
 ('AOL','AO1 AO2',C_MOT),('BOL','BO1 BO2',C_MOT)])

gy = box(1060,500,330,175,'GY-521 MPU6050','插座 J11 · I²C 0x68',[
 ('VCC','VCC',C_PWR),('GND','GND / AD0',C_GND),
 ('SCL','SCL',C_I2C),('SDA','SDA',C_I2C),('NC','XDA XCL INT 悬空',DIM)])

ina = box(590,745,300,180,'INA226 (CJMCU-226)','逻辑插座 J10 + 动力端子 J6',[
 ('VCC','VCC',C_PWR),('GND','GND',C_GND),
 ('SDA','SDA',C_I2C),('SCL','SCL',C_I2C),
 ('VINP','VIN+ ← 电池+',C_PWR),('VINM','VIN− → VM',C_PWR)])

sd = box(1060,725,330,205,'microSD 模块','插座 J5 + 杜邦线(按丝印)',[
 ('VCC','VCC (JP1选)',C_PWR),('GND','GND',C_GND),('CS','CS',C_SPI),
 ('SCK','SCK',C_SPI),('MOSI','MOSI',C_SPI),('MISO','MISO',C_SPI)])

bat = box(110,100,340,250,'电源输入','端子 J8 (KF301) + 跳线 J9',[
 ('BATP','BAT+ 7.4–8.4V',C_PWR),('GND','GND',C_GND),
 ('SW','逻辑电源跳线',C_PWR)])

mp = box(110,470,340,175,'MP1584 降压 → 5V','插座 J4 + 杜邦线',[
 ('INP','IN+',C_PWR),('ING','IN−',C_GND),
 ('OUTP','OUT+ 5V',C_PWR),('OUTG','OUT−',C_GND)])

enc = box(110,745,340,180,'编码器端子 ×2','J2 左 / J3 右 (KF3500)',[
 ('3V3','3V3',C_PWR),('GND','GND',C_GND),
 ('EA','A 相',C_ENC),('EB','B 相',C_ENC)])

# ---------------- 直角连线 ----------------
def rt(p1,p2,c,vy=None,w=2.2,dash=None):
    x1,y1=p1; x2,y2=p2
    if vy is not None:
        L(x1,y1,x1,vy,c,w,dash); L(x1,vy,x2,vy,c,w,dash); L(x2,vy,x2,y2,c,w,dash)
    else:
        mx=(x1+x2)/2; L(x1,y1,mx,y1,c,w,dash); L(mx,y1,mx,y2,c,w,dash); L(mx,y2,x2,y2,c,w,dash)

for a,b,c,vy in [
 (esp['AIN1R'],drv['AIN1'],C_SIG,1015),
 (esp['AIN2R'],drv['AIN2'],C_SIG,1000),
 (esp['BIN1R'],drv['BIN1'],C_SIG,985),
 (esp['BIN2R'],drv['BIN2'],C_SIG,970),
 (esp['SDAR'], gy['SDA'], C_I2C,957),
 (esp['SCLR'], gy['SCL'], C_I2C,949),
 (esp['SDAR'], ina['SDA'],C_I2C,552),
 (esp['SCLR'], ina['SCL'],C_I2C,545),
 (esp['CSR'],  sd['CS'],  C_SPI,700),
 (esp['SCKR'], sd['SCK'], C_SPI,690),
 (esp['MOSIR'],sd['MOSI'],C_SPI,680),
 (esp['MISOR'],sd['MISO'],C_SPI,670),
 (enc['EAR'],  esp['ELA'],C_ENC,935),
 (enc['EBR'],  esp['ELB'],C_ENC,928),
]: rt(a,b,c,vy)

# GND 母线
BUSY=1014
L(80,BUSY,1420,BUSY,C_GND,4)
T(88,BUSY-8,'GND 公共地 · 底层整板铺铜',12,C_GND)
for an,key in [(bat,'GND'),(mp,'ING'),(enc,'GND'),(esp,'GND'),(drv,'GND'),(gy,'GND'),(ina,'GND'),(sd,'GND')]:
    x,y=an[key]
    L(x,y,x,BUSY,C_GND,2,'4,5'); A('<circle cx="%.1f" cy="%d" r="4" fill="%s"/>'%(x,BUSY,C_GND))

# 3V3 母线（顶部）
B3=66
L(80,B3,1420,B3,C_PWR,4)
T(88,B3-7,'3V3（ESP32 板载稳压输出，经插座分配）',12,C_PWR)
for an,key in [(esp,'3V3'),(drv,'STBY'),(gy,'VCC'),(ina,'VCC'),(enc,'3V3')]:
    x,y=an[key]
    L(x,y,x,B3,C_PWR,2,'4,5'); A('<circle cx="%.1f" cy="%d" r="4" fill="%s"/>'%(x,B3,C_PWR))

# VBAT 主干
VB=166
x,y = bat['BATPR']
L(x,y,590,VB,C_PWR,4)
L(590,VB,1060,VB,C_PWR,4)
A('<circle cx="%.0f" cy="%d" r="4" fill="%s"/>'%(590,VB,C_PWR))
# → INA226 VIN+（串联）
_vy = ina['VINP'][1]
L(590,VB,590,_vy,C_PWR,3,'7,4')
L(590,_vy,ina['VINP'][0],_vy,C_PWR,3,'7,4')
# → DRV VM
L(1060,VB,1060,drv['VM'][1],C_PWR,4)
x,y = drv['VM']
L(1060,y,x,y,C_PWR,4)
# VM → INA VIN−（测量回路）
L(drv['VM'][0]+3,drv['VM'][1]-14,drv['VM'][0]+3,drv['VM'][1]-14,C_PWR,1)
T(596,180,'VBAT',12,C_PWR,'start','600')
T(700,180,'← J9 跳线=逻辑供电 · 主干→INA226 VIN+→(模块)→VIN−→VM',12,C_PWR)
# VM 回线说明（文字）
T(1066,150,'VM（经 INA226 测量后）',12,C_PWR,'start','600')

# J9 → MP1584 IN+
x1,y1 = bat['SWR']; x2,y2 = mp['INP']
L(x1,y1,x1,y2,C_PWR,3,'6,4'); L(x1,y2,x2,y2,C_PWR,3,'6,4')
T((x1+x2)/2+6,(y1+y2)/2,'J9 跳线帽=开机',11,DIM,'middle')

# MP1584 OUT → ESP32 VIN
x1,y1 = mp['OUTPR']; x2,y2 = esp['VIN']
L(x1,y1,560,y1,C_PWR,3); L(560,y1,560,y2,C_PWR,3); L(560,y2,x2,y2,C_PWR,3)
T(566,int((y1+y2)/2),'5V',12,C_PWR,'start','600')

# 电机线
L(drv['AOLR'][0],drv['AOLR'][1],1420,drv['AOLR'][1],C_MOT,4)
T(1414,drv['AOLR'][1]-8,'→ J13 左电机 M+/M−',11,C_MOT,'end')
L(drv['BOLR'][0],drv['BOLR'][1],1420,drv['BOLR'][1],C_MOT,4)
T(1414,drv['BOLR'][1]-8,'→ J14 右电机 M+/M−',11,C_MOT,'end')

# JP1 说明
R(1428,745,50,60,4,'#1c2330',C_PWR)
T(1400,838,'JP1 焊锡桥：SD-VCC = 3V3 或 5V（按 microSD 模块版本）',11,DIM,'end')

# 图例
LG=[('电源 VBAT/5V/3V3',C_PWR),('GND',C_GND),('电机控制',C_SIG),('I²C',C_I2C),('SPI',C_SPI),('编码器',C_ENC),('电机动力',C_MOT)]
for i,(t,c) in enumerate(LG):
    A('<rect x="%d" y="%d" width="18" height="6" rx="2" fill="%s"/>'%(40+150*i, 90, c))
    T(64+150*i, 96, t, 10.5, DIM)

A('</svg>')
os.makedirs('out',exist_ok=True)
open('out/schematic.svg','w').write('\n'.join(out))
print('ok -> out/schematic.svg')
