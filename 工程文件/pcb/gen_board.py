# -*- coding: utf-8 -*-
"""
gen_board.py — IPQ-2026 小车模块载板（面包板 → PCB）
================================================================
输出：
  out/gerber/*  RS-274X 光绘 + Excellon 钻孔 → out/IPQ_CARRIER_V1_gerber.zip
  out/preview_top.png / preview_bottom.png / report.txt
板子：95 x 80 mm，2 层，1.6mm。底层整板 GND 铺铜（自动让位 + 热焊盘辐条）。
与固件 ipq_robot_test v3.3 引脚一一对应。
"""
import math, os, zipfile
from gerblib import Gerber, Excellon, text_strokes

BOARD_W, BOARD_H = 95.0, 80.0

# ---- 工艺参数（嘉立创经济板能力内，留裕量）----
CLR        = 0.20
SIG_W      = 0.40
PWR_W      = 0.80
MOT_W      = 1.80
VIA_D, VIA_PAD = 0.6, 1.0
HDR_PAD    = 1.7
DRV_PAD    = 1.8
KF5_PAD    = 2.9
KF35_PAD   = 2.6
CAP_PAD    = 1.9
MH_D       = 3.2

# ============================================================================
# 1. 焊盘
# ============================================================================
pads = []
def P(ref, pin, x, y, net, drill=1.0, pad=HDR_PAD):
    pads.append(dict(ref=ref, pin=pin, x=x, y=y, net=net, drill=drill, pad=pad))

P2 = 2.54

# ---- ESP32 DevKit V1 30P 插座（2x15，列距 22.86，USB 朝板上边缘）----
EX_L, EX_R, EY0 = 15.0, 37.86, 16.0
LEFT_PINS  = ['EN','VP','VN','D34','D35','D32','D33','D25','D26','D27','D14','D12','D13','GND','VIN']
RIGHT_PINS = ['D23','D22','TX0','RX0','D21','D19','D18','D5','TX2','RX2','D4','D2','D15','GND','3V3']
LEFT_NETS  = ['NC','NC','NC','ENCL_A','ENCL_B','ENCR_A','ENCR_B','NC','NC','SPI_CS','SPI_SCK','NC','NC','GND','P5V']
RIGHT_NETS = ['AIN1','SCL','NC','NC','SDA','AIN2','BIN1','NC','NC','BIN2','NC','SPI_MISO','SPI_MOSI','GND','P3V3']
for i,(nm,net) in enumerate(zip(LEFT_PINS, LEFT_NETS)):
    P('ESP32', nm, EX_L, EY0+i*P2, net)
for i,(nm,net) in enumerate(zip(RIGHT_PINS, RIGHT_NETS)):
    P('ESP32', nm, EX_R, EY0+i*P2, net)

# ---- DRV8833 (D2-1-2F) 插座 2x8，列距 10.16 ----
DX_L, DX_R, DY0 = 52.0, 62.16, 12.0
DRV_L = ['NC','AIN2','AIN1','STBY','BIN1','BIN2','NC','GND']
DRV_R = ['VM','NC','GND','AO1','AO2','BO2','BO1','GND']
DRV_LN = ['NC','AIN2','AIN1','P3V3','BIN1','BIN2','NC','GND']
DRV_RN = ['VM','NC','GND','MOTL_P','MOTL_N','MOTR_N','MOTR_P','GND']
for j,(nm,net) in enumerate(zip(DRV_L, DRV_LN)):
    P('DRV', nm, DX_L, DY0+j*P2, net, pad=DRV_PAD)
for j,(nm,net) in enumerate(zip(DRV_R, DRV_RN)):
    P('DRV', nm, DX_R, DY0+j*P2, net, pad=DRV_PAD)

# ---- GY-521 (MPU6050) 插座 1x8（模块本体在引脚行南侧）----
GY_X0, GY_Y = 46.0, 40.0
GY_PINS = ['VCC','GND','SCL','SDA','XDA','XCL','AD0','INT']
GY_NETS = ['P3V3','GND','SCL','SDA','NC','NC','GND','NC']
for k,(nm,net) in enumerate(zip(GY_PINS, GY_NETS)):
    P('GY521', nm, GY_X0+k*P2, GY_Y, net)

# ---- microSD 模块插座 1x6（杜邦线按丝印对接）----
SD_X0, SD_Y = 34.0, 66.0
SD_PINS = ['VCC','GND','CS','SCK','MOSI','MISO']
SD_NETS = ['SD_VCC','GND','SPI_CS','SPI_SCK','SPI_MOSI','SPI_MISO']
for k,(nm,net) in enumerate(zip(SD_PINS, SD_NETS)):
    P('SD', nm, SD_X0+k*P2, SD_Y, net)

# ---- microSD VCC 选择跳线 JP1：2=SD_VCC 3=3V3 4=5V ----
JP_Y = 72.5
P('JP1','2', 34.0,  JP_Y, 'SD_VCC', pad=1.8)
P('JP1','3', 36.54, JP_Y, 'P3V3',   pad=1.8)
P('JP1','4', 39.08, JP_Y, 'P5V',    pad=1.8)

# ---- INA226 逻辑插座 1x4（与 GY 同网格对齐便于布线）----
INA_X0, INA_Y = 51.08, 66.0
INA_PINS = ['SCL','SDA','GND','VCC']
INA_NETS = ['SCL','SDA','GND','P3V3']
for k,(nm,net) in enumerate(zip(INA_PINS, INA_NETS)):
    P('INA', nm, INA_X0+k*P2, INA_Y, net)

# ---- MP1584 模块插座 1x4 ----
MP_X0, MP_Y = 14.0, 66.0
MP_PINS = ['IN+','IN-','OUT+','OUT-']
MP_NETS = ['VSW','GND','P5V','GND']
for k,(nm,net) in enumerate(zip(MP_PINS, MP_NETS)):
    P('MP', nm, MP_X0+k*P2, MP_Y, net)

# ---- INA226 动力串联端子 ----
P('JT_INA','VIN+', 77.0,  9.0, 'VBAT', drill=1.5, pad=KF5_PAD)
P('JT_INA','VIN-', 82.08, 9.0, 'VM',   drill=1.5, pad=KF5_PAD)

# ---- 电机输出端子 ----
P('JT_ML','M+', 77.0,  16.0, 'MOTL_P', drill=1.5, pad=KF5_PAD)
P('JT_ML','M-', 82.08, 16.0, 'MOTL_N', drill=1.5, pad=KF5_PAD)
P('JT_MR','M+', 77.0,  26.0, 'MOTR_P', drill=1.5, pad=KF5_PAD)
P('JT_MR','M-', 82.08, 26.0, 'MOTR_N', drill=1.5, pad=KF5_PAD)

# ---- 编码器端子 4P-3.5mm（西边缘），引脚顺序 A B GND 3V3 ----
for (x0,y0,name) in [(10.0,30.0,'L'),(10.0,46.0,'R')]:
    nets = {'L':['ENCL_A','ENCL_B','GND','P3V3'],'R':['ENCR_A','ENCR_B','GND','P3V3']}[name]
    for k,(nm,net) in enumerate(zip(['A','B','GND','3V3'], nets)):
        P('ENC-'+name, nm, x0, y0+k*3.5, net, drill=1.3, pad=KF35_PAD)

# ---- 电池输入端子 + 逻辑电源跳线 ----
P('JT_BAT','BAT+', 77.0,  70.0, 'VBAT', drill=1.5, pad=KF5_PAD)
P('JT_BAT','GND',  82.08, 70.0, 'GND',  drill=1.5, pad=KF5_PAD)
P('J_SW','1', 70.54, 73.5,  'VBAT', pad=1.8)
P('J_SW','2', 68.00, 73.5,  'VSW',  pad=1.8)

# ---- VM 滤波电容（VM 干线 y=6.0 北侧）----
P('C1','+', 73.5, 6.0,  'VM',  drill=0.9, pad=CAP_PAD)   # 100uF/16V
P('C1','-', 73.5, 11.0, 'GND', drill=0.9, pad=CAP_PAD)
P('C2','+', 70.0, 6.0,  'VM',  drill=0.9, pad=CAP_PAD)   # 100nF
P('C2','-', 70.0, 8.54, 'GND', drill=0.9, pad=CAP_PAD)

# ============================================================================
# 2. 过孔
# ============================================================================
vias = []
def V(x, y, net):
    vias.append(dict(x=x, y=y, net=net))

gnd_stub = []
for (px,py,offx,offy) in [
    (15.0,49.02, 2.5,0),       # ESP32 左列 GND
    (37.86,49.02,-2.36,0),     # ESP32 右列 GND
    (52.0,29.78, 0,1.72),      # DRV 左列 GND
    (62.16,29.78,0,1.72),      # DRV 右列 GND
    (48.54,40.0, 0,2.0),       # GY GND
    (61.24,40.0, 0,2.0),       # GY AD0->GND
    (36.54,66.0, 0,2.6),       # SD GND
    (16.54,66.0, 0,2.8),       # MP IN-
    (21.62,66.0, 1.88,1.0),    # MP OUT-（斜向避让 5V 线）
    (56.16,66.0, 0,1.2),       # INA GND
    (70.0,8.54, 0,1.36),       # C2 -
    (73.5,11.0, 0,1.35),       # C1 -
    (82.08,70.0,0,2.5),        # 电池 GND
    (10.0,37.0, -1.4,0),       # ENC-L GND
    (10.0,53.0, -1.4,0),       # ENC-R GND
]:
    sx, sy = px+offx, py+offy
    gnd_stub.append((px,py,sx,sy))
    V(sx, sy, 'GND')

# 信号/电源过孔
V(40.2, 18.54, 'SCL')
V(42.3, 26.16, 'SDA')
V(39.2, 28.70, 'AIN2')
V(44.16, 46.48, 'SPI_MOSI')
V(46.70, 43.94, 'SPI_MISO')
V(49.0, 51.56, 'P3V3')     # 3V3 主干下底层
V(41.3, 51.56, 'P3V3')     # STBY 支路下底层
V(12.0, 46.0, 'ENCR_A')
V(13.4, 49.5, 'ENCR_B')
V(77.0, 74.2, 'VBAT')
V(85.0, 74.2, 'VBAT')
V(85.0, 12.0, 'VBAT')

# ============================================================================
# 3. 布线
# ============================================================================
tracks = []
def T(net, layer, w, *pts):
    tracks.append(dict(net=net, layer=layer, w=w, pts=list(pts)))

# ---- ESP32 → DRV 控制 ----
T('AIN1','T',SIG_W, (37.86,16.0),(52.0,16.0),(52.0,17.08))
T('AIN2','B',SIG_W, (39.2,28.70),(39.2,14.54),(52.0,14.54))
T('BIN1','T',SIG_W, (37.86,31.24),(43.5,31.24),(43.5,22.16),(52.0,22.16))
T('BIN2','T',SIG_W, (37.86,38.86),(45.3,38.86),(45.3,24.70),(52.0,24.70))

# ---- I2C（底层；竖线穿过 GY 自身焊盘=同网络）----
T('SCL','T',SIG_W, (37.86,18.54),(40.2,18.54))
T('SCL','B',SIG_W, (40.2,18.54),(40.2,33.5),(51.08,33.5),(51.08,66.0))
T('SDA','T',SIG_W, (37.86,26.16),(42.3,26.16))
T('SDA','B',SIG_W, (42.3,26.16),(42.3,24.0),(50.4,24.0),(50.4,9.5),(53.62,9.5),(53.62,66.0))

# ---- SPI ----
T('SPI_CS','T',SIG_W, (15.0,38.86),(20.0,38.86),(20.0,63.5),(39.08,63.5),(39.08,66.0))
T('SPI_SCK','T',SIG_W, (15.0,41.40),(22.5,41.40),(22.5,62.0),(41.62,62.0),(41.62,66.0))
T('SPI_MOSI','T',SIG_W, (37.86,46.48),(44.16,46.48))
T('SPI_MOSI','B',SIG_W, (44.16,46.48),(44.16,66.0))
T('SPI_MISO','T',SIG_W, (37.86,43.94),(46.70,43.94))
T('SPI_MISO','B',SIG_W, (46.70,43.94),(46.70,66.0))

# ---- 3V3 ----
T('P3V3','T',PWR_W, (37.86,51.56),(50.3,51.56))                       # 顶层主干
# 底层西干线（编码器 VCC / JP1-3V3 / INA VCC）
T('P3V3','B',PWR_W, (49.0,51.56),(49.0,68.5))
T('P3V3','B',SIG_W, (49.0,68.5),(58.70,68.5),(58.70,66.0))            # INA VCC
T('P3V3','B',SIG_W, (49.0,68.5),(49.0,70.8),(36.54,70.8),(36.54,72.5))# JP1 pad3
T('P3V3','B',SIG_W, (49.0,70.8),(6.2,70.8),(6.2,40.5),(10.0,40.5))    # ENC-L 3V3
T('P3V3','B',SIG_W, (6.2,56.5),(10.0,56.5))                           # ENC-R 3V3
# STBY 支路（底层绕行）
T('P3V3','B',SIG_W, (41.3,51.56),(41.3,34.5),(49.3,34.5),(49.3,19.62),(52.0,19.62))
# GY VCC 支路（底层）
T('P3V3','B',SIG_W, (41.3,41.5),(46.0,41.5),(46.0,40.0))

# ---- 5V：MP1584 OUT+ → ESP32 VIN；底层分支 → JP1 pad4 ----
T('P5V','T',PWR_W, (19.08,66.0),(19.08,64.3),(12.4,64.3),(12.4,51.56),(15.0,51.56))
T('P5V','T',SIG_W, (19.08,66.0),(19.08,68.3),(26.5,68.3),(26.5,75.6),(40.7,75.6),(40.7,72.5),(39.08,72.5))

# ---- VSW：电源跳线 → MP1584 IN+（沿南缘绕行）----
T('VSW','T',0.5, (68.0,73.5),(68.0,77.1),(12.0,77.1),(12.0,66.0),(14.0,66.0))

# ---- VBAT：电池+ → 逻辑跳线 / 东侧底层干线 → INA226 VIN+ ----
T('VBAT','T',0.5, (77.0,70.0),(71.8,70.0),(71.8,73.5),(70.54,73.5))
T('VBAT','T',0.8, (77.0,70.0),(77.0,74.2))
T('VBAT','B',0.8, (77.0,74.2),(85.0,74.2))
T('VBAT','B',MOT_W, (85.0,74.2),(85.0,12.0))
T('VBAT','T',0.8, (85.0,12.0),(77.0,12.0),(77.0,9.0))

# ---- VM：INA226 VIN- → DRV VM（电容焊盘直接压在干线上）----
T('VM','T',MOT_W, (82.08,9.0),(82.08,6.0),(64.5,6.0),(64.5,12.0),(62.16,12.0))

# ---- 电机输出 ----
T('MOTL_P','T',MOT_W, (62.16,19.62),(72.5,19.62),(72.5,16.0),(77.0,16.0))
T('MOTL_N','T',MOT_W, (62.16,22.16),(67.0,22.16),(67.0,23.3),(87.0,23.3),(87.0,16.0),(82.08,16.0))
T('MOTR_N','T',MOT_W, (62.16,24.70),(64.3,24.70),(64.3,31.5),(88.5,31.5),(88.5,26.0),(82.08,26.0))
T('MOTR_P','T',MOT_W, (62.16,27.24),(70.0,27.24),(70.0,26.0),(77.0,26.0))

# ---- 编码器（西缘）----
T('ENCL_A','T',SIG_W, (10.0,30.0),(12.0,30.0),(12.0,23.62),(15.0,23.62))
T('ENCL_B','T',SIG_W, (10.0,33.5),(13.4,33.5),(13.4,26.16),(15.0,26.16))
T('ENCR_A','T',SIG_W, (10.0,46.0),(12.0,46.0))
T('ENCR_A','B',SIG_W, (12.0,46.0),(12.0,28.70),(15.0,28.70))
T('ENCR_B','T',SIG_W, (10.0,49.5),(13.4,49.5))
T('ENCR_B','B',SIG_W, (13.4,49.5),(13.4,31.24),(15.0,31.24))

# ---- GND stubs ----
for (x1,y1,x2,y2) in gnd_stub:
    T('GND','T',SIG_W, (x1,y1),(x2,y2))

# ---- SD_VCC ----
T('SD_VCC','T',0.5, (34.0,66.0),(34.0,72.5))

# ============================================================================
# 4. 丝印
# ============================================================================
silk_lines, silk_texts = [], []
def SL(x1,y1,x2,y2,w=0.2):
    silk_lines.append((x1,y1,x2,y2,w))
def ST(t,x,y,h=1.0,rot=0):
    silk_texts.append((t,x,y,h,rot))
def text_w(t,h):
    segs = text_strokes(t,0,0,h)
    return max((s[2] for s in segs), default=0)

def dash_rect(x1,y1,x2,y2,label,label_h=1.4):
    step = 2.0
    for (ax,ay,bx,by) in [(x1,y1,x2,y1),(x2,y1,x2,y2),(x2,y2,x1,y2),(x1,y2,x1,y1)]:
        L = math.hypot(bx-ax, by-ay)
        n = max(2, int(L/step))
        for i in range(n):
            t0, t1 = i/n, (i+0.55)/n
            SL(ax+(bx-ax)*t0, ay+(by-ay)*t0, ax+(bx-ax)*t1, ay+(by-ay)*t1)
    ST(label, x1+0.6, y1+0.5, label_h)

dash_rect(10.8, 6.8, 42.2, 60.2, 'ESP32 DevKit V1 30P (USB THIS END)')
dash_rect(49.4, 9.4, 64.8, 32.4, 'DRV8833 SILK-UP')
dash_rect(44.0, 40.4, 65.9, 56.2, 'GY-521 MPU6050')
dash_rect(32.8, 64.7, 47.9, 67.3, 'microSD', 1.1)
dash_rect(12.9, 64.7, 22.8, 67.3, 'MP1584', 1.1)
dash_rect(49.9, 64.7, 60.8, 67.3, 'INA226', 1.1)
# 电容外形
for (cx,cy,r) in [(73.5,8.5,4.2)]:
    for i in range(24):
        a0,a1 = i/24*2*math.pi, (i+0.6)/24*2*math.pi
        SL(cx+r*math.cos(a0), cy+r*math.sin(a0), cx+r*math.cos(a1), cy+r*math.sin(a1))
SL(69.2,4.6,70.8,4.6); SL(70.0,3.8,70.0,5.4)
ST('C1 100U', 66.2, 13.4, 1.0)
ST('C2 100N', 66.2, 2.4, 1.0)

# ESP32 引脚丝印
for i,nm in enumerate(LEFT_PINS):
    y = EY0+i*P2
    w = text_w(nm,1.0)
    for (a,b,c,d) in text_strokes(nm, 0, y-0.5, 1.0):
        SL(13.9-w+a, b, 13.9-w+c, d)
for i,nm in enumerate(RIGHT_PINS):
    y = EY0+i*P2
    for (a,b,c,d) in text_strokes(nm, 39.1, y-0.5, 1.0):
        SL(a,b,c,d)
# DRV 引脚丝印
for j,nm in enumerate(DRV_L):
    y = DY0+j*P2
    w = text_w(nm,0.9)
    for (a,b,c,d) in text_strokes(nm, 0, y-0.45, 0.9):
        SL(51.1-w+a, b, 51.1-w+c, d)
for j,nm in enumerate(DRV_R):
    y = DY0+j*P2
    for (a,b,c,d) in text_strokes(nm, 63.1, y-0.45, 0.9):
        SL(a,b,c,d)
# GY / SD / INA / MP 引脚丝印（引脚上方或下方）
for k,nm in enumerate(GY_PINS):
    for (a,b,c,d) in text_strokes(nm, GY_X0+k*P2-0.9, 41.3, 0.9):
        SL(a,b,c,d)
for nm,x0 in [('SD',SD_X0),('INA',INA_X0),('MP',MP_X0)]:
    pins = {'SD':SD_PINS,'INA':INA_PINS,'MP':MP_PINS}[nm]
    for k,p in enumerate(pins):
        w = text_w(p,0.9)
        for (a,b,c,d) in text_strokes(p, 0, 0, 0.9):
            SL(x0+k*P2 - w/2 + a, 62.4+b, x0+k*P2 - w/2 + c, 62.4+d)

def term_label(x, y, txt, dx, dy, h=1.1):
    w = text_w(txt,h)
    for (a,b,c,d) in text_strokes(txt, 0, 0, h):
        SL(x+dx-w/2+a, y+dy+b, x+dx-w/2+c, y+dy+d)

term_label(77.0, 9.0,  'V+IN', 0, -3.4);  term_label(82.08, 9.0,  'V-OUT', 0, -3.4)
term_label(77.0, 16.0, 'L-M+', 0, -3.4);  term_label(82.08, 16.0, 'L-M-', 0, -3.4)
term_label(77.0, 26.0, 'R-M+', 0, -3.4);  term_label(82.08, 26.0, 'R-M-', 0, -3.4)
term_label(77.0, 70.0, 'BAT+', 0, 3.6);   term_label(82.08, 70.0, 'GND', 0, 3.6)
ST('INA226 PATH: BAT+ -> VIN+ | VIN- -> VM', 43.0, 3.4, 1.2)
# 编码器端子标注
for y0,name in [(30.0,'L'),(46.0,'R')]:
    for k,nm in enumerate(['A','B','GND','3V3']):
        w = text_w(nm,0.9)
        for (a,b,c,d) in text_strokes(nm, 0, 0, 0.9):
            SL(6.7-w + a, y0+k*3.5-0.45+b, 6.7-w + c, y0+k*3.5-0.45+d)
    t = 'ENC-'+name; w = text_w(t,1.1)
    for (a,b,c,d) in text_strokes(t, 0,0,1.1):
        SL(10.0-w/2+a, y0-2.8+b, 10.0-w/2+c, y0-2.8+d)
# JP1 / SW 标注
ST('SD-VCC SEL', 32.6, 69.4, 1.0)
ST('3V3', 35.9, 75.0, 1.0); ST('5V', 38.6, 75.0, 1.0)
ST('LOGIC PWR JUMPER=ON', 58.0, 75.4, 1.0)
# 标题
ST('IPQ-2026 ROBOT CARRIER v1.0', 44.0, 77.6, 1.6)
ST('2026-08-21  2-Layer 1.6mm', 44.0, 76.0, 1.0)
for (mx,my) in [(5,5),(90,5),(5,75),(90,75)]:
    SL(mx-1.0,my,mx+1.0,my,0.25); SL(mx,my-1.0,mx,my+1.0,0.25)

npths = [(5,5),(90,5),(5,75),(90,75)]

# ============================================================================
# 6. DRC-lite
# ============================================================================
def seg_pt_dist(px,py, ax,ay,bx,by):
    abx, aby = bx-ax, by-ay
    L2 = abx*abx+aby*aby
    if L2 == 0: return math.hypot(px-ax,py-ay)
    t = max(0, min(1, ((px-ax)*abx+(py-ay)*aby)/L2))
    return math.hypot(px-(ax+abx*t), py-(ay+aby*t))

def seg_seg_dist(a, b, c, d):
    (ax,ay),(bx,by) = a,b; (cx,cy),(dx,dy) = c,d
    return min(seg_pt_dist(cx,cy,ax,ay,bx,by), seg_pt_dist(dx,dy,ax,ay,bx,by),
               seg_pt_dist(ax,ay,cx,cy,dx,dy), seg_pt_dist(bx,by,cx,cy,dx,dy))

def copper_items(layer):
    items = []
    for p in pads:
        items.append(('pad', p['net'], p['x'], p['y'], p['pad']/2.0, p['ref']+'.'+p['pin']))
    for v in vias:
        items.append(('pad', v['net'], v['x'], v['y'], VIA_PAD/2.0, 'via@%.1f,%.1f'%(v['x'],v['y'])))
    for t in tracks:
        if t['layer'] != layer: continue
        pts = t['pts']
        for i in range(len(pts)-1):
            items.append(('seg', t['net'], pts[i], pts[i+1], t['w']/2.0, '%s-%s#%d'%(t['net'],t['layer'],i)))
    return items

def run_drc():
    errs, warns = [], []
    for layer in ('T','B'):
        items = copper_items(layer)
        n = len(items)
        for i in range(n):
            for j in range(i+1, n):
                a, b = items[i], items[j]
                if a[1] == b[1]:
                    continue
                if a[0]=='pad' and b[0]=='pad':
                    d = math.hypot(a[2]-b[2], a[3]-b[3]) - a[4] - b[4]
                elif a[0]=='pad' and b[0]=='seg':
                    d = seg_pt_dist(a[2],a[3], b[2][0],b[2][1],b[3][0],b[3][1]) - a[4] - b[4]
                elif a[0]=='seg' and b[0]=='pad':
                    d = seg_pt_dist(b[2],b[3], a[2][0],a[2][1],a[3][0],a[3][1]) - b[4] - a[4]
                else:
                    d = seg_seg_dist(a[2],a[3],b[2],b[3]) - a[4] - b[4]
                if d < CLR - 1e-6:
                    errs.append('%s 层间距 %.3fmm: %s <-> %s' % (layer, d, a[5], b[5]))
    for p in pads:
        ring = (p['pad']-p['drill'])/2
        if ring < 0.30:
            errs.append('环宽不足 %s.%s ring=%.2f' % (p['ref'],p['pin'],ring))
    EDGE = 0.4
    def edge_chk(x,y,r,tag):
        for (bx,by) in [(x,0),(x,BOARD_H),(0,y),(BOARD_W,y)]:
            d = math.hypot(x-bx,y-by) - r
            if d < EDGE-1e-6:
                errs.append('距板边 %.2f: %s'%(d,tag)); break
    for p in pads: edge_chk(p['x'],p['y'],p['pad']/2, p['ref']+'.'+p['pin'])
    for v in vias: edge_chk(v['x'],v['y'],VIA_PAD/2, 'via')
    for t in tracks:
        for (x,y) in t['pts']:
            edge_chk(x,y,t['w']/2, t['net']+t['layer'])
    for (mx,my) in npths:
        for layer in ('T','B'):
            for it in copper_items(layer):
                if it[0]=='pad':
                    d = math.hypot(it[2]-mx, it[3]-my) - it[4] - MH_D/2
                else:
                    d = seg_pt_dist(mx,my,it[2][0],it[2][1],it[3][0],it[3][1]) - it[4] - MH_D/2
                if d < 0.25-1e-6:
                    errs.append('安装孔让位 %.2f: %s (%s)'%(d,it[5],layer))
    return errs, warns

# ============================================================================
# 7. 预览渲染（PIL）
# ============================================================================
def render(path, layer, mirror=False):
    S = 14
    from PIL import Image, ImageDraw
    W,H = int(BOARD_W*S)+40, int(BOARD_H*S)+40
    img = Image.new('RGB',(W,H), (8,64,32) if layer=='T' else (32,48,64))
    dr = ImageDraw.Draw(img)
    def xy(x,y):
        if mirror: x = BOARD_W - x
        return (20+x*S, 20+y*S)
    if layer=='B':
        dr.polygon([xy(0.5,0.5),xy(BOARD_W-0.5,0.5),xy(BOARD_W-0.5,BOARD_H-0.5),xy(0.5,BOARD_H-0.5)],
                   fill=(52,84,110))
        for p in pads:
            if p['net']=='GND': continue
            x,y = xy(p['x'],p['y']); r=(p['pad']/2+0.45)*S
            dr.ellipse([x-r,y-r,x+r,y+r], fill=(32,48,64))
        for v in vias:
            if v['net']=='GND': continue
            x,y = xy(v['x'],v['y']); r=(VIA_PAD/2+0.45)*S
            dr.ellipse([x-r,y-r,x+r,y+r], fill=(32,48,64))
        for t in tracks:
            if t['layer']!='B': continue
            pts=[xy(*p) for p in t['pts']]
            dr.line(pts, fill=(200,60,40), width=max(2,int(t['w']*S)))
            for p in pts:
                r = t['w']/2*S
                dr.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r], fill=(200,60,40))
        for (mx,my) in npths:
            x,y = xy(mx,my); r=(MH_D/2+0.6)*S
            dr.ellipse([x-r,y-r,x+r,y+r], fill=(32,48,64))
    for t in tracks:
        if t['layer']!=layer: continue
        pts=[xy(*p) for p in t['pts']]
        dr.line(pts, fill=(220,120,60), width=max(2,int(t['w']*S)))
        for p in pts:
            r = t['w']/2*S
            dr.ellipse([p[0]-r,p[1]-r,p[0]+r,p[1]+r], fill=(220,120,60))
    for p in pads:
        x,y = xy(p['x'],p['y']); r=p['pad']/2*S
        dr.ellipse([x-r,y-r,x+r,y+r], fill=(240,200,80))
        rr = p['drill']/2*S
        dr.ellipse([x-rr,y-rr,x+rr,y+rr], fill=(10,10,10))
    for v in vias:
        x,y = xy(v['x'],v['y']); r=VIA_PAD/2*S
        dr.ellipse([x-r,y-r,x+r,y+r], fill=(240,160,60))
        rr=VIA_D/2*S; dr.ellipse([x-rr,y-rr,x+rr,y+rr], fill=(10,10,10))
    for (mx,my) in npths:
        x,y=xy(mx,my); r=MH_D/2*S
        dr.ellipse([x-r,y-r,x+r,y+r], outline=(230,230,230), width=2)
    for (x1,y1,x2,y2,w) in silk_lines:
        a,b = xy(x1,y1); c,d = xy(x2,y2)
        dr.line([a,b,c,d], fill=(235,235,235), width=2)
    for (t,x,y,h,rot) in silk_texts:
        for (a,b,c,d) in text_strokes(t,x,y,h,rot):
            p1,p2 = xy(a,b), xy(c,d)
            dr.line([p1,p2], fill=(235,235,235), width=2)
    a, b = xy(0,0), xy(BOARD_W,BOARD_H)
    dr.rectangle([min(a[0],b[0]), min(a[1],b[1]), max(a[0],b[0]), max(a[1],b[1])],
                 outline=(180,180,180), width=2)
    img.save(path)

# ============================================================================
# 8. Gerber 输出
# ============================================================================
MASK_EXP = 0.10
def emit():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
    gdir = os.path.join(out, 'gerber')
    os.makedirs(gdir, exist_ok=True)

    # 铜顶层
    g = Gerber()
    for t in tracks:
        if t['layer']=='T':
            g.draw(t['pts'], t['w'])
    for p in pads:
        g.flash(p['x'],p['y'], g.circle(p['pad']))
    for v in vias:
        g.flash(v['x'],v['y'], g.circle(VIA_PAD))
    g.save(os.path.join(gdir,'IPQ-CARRIER_V1.GTL'), {'FileFunction':'Copper,L1,Top'})

    # 铜底层：铺铜 + 让位 + 热焊盘 + 走线
    g = Gerber()
    g.region([(0.5,0.5),(BOARD_W-0.5,0.5),(BOARD_W-0.5,BOARD_H-0.5),(0.5,BOARD_H-0.5)])
    g.polarity('C')
    for p in pads:
        if p['net']=='GND': continue
        g.flash(p['x'],p['y'], g.circle(p['pad']+2*0.45))
    for v in vias:
        if v['net']=='GND': continue
        g.flash(v['x'],v['y'], g.circle(VIA_PAD+2*0.45))
    for t in tracks:
        if t['layer']=='B':
            g.draw(t['pts'], t['w']+2*0.45)
    for (mx,my) in npths:
        g.flash(mx,my, g.circle(MH_D+2*0.6))
    g.draw([(0.3,0.3),(BOARD_W-0.3,0.3),(BOARD_W-0.3,BOARD_H-0.3),(0.3,BOARD_H-0.3),(0.3,0.3)], 0.8)
    g.polarity('D')
    for p in [p for p in pads if p['net']=='GND']:
        g.polarity('C'); g.flash(p['x'],p['y'], g.circle(p['pad']+2*0.55))
        g.polarity('D')
        r_in, r_out = p['pad']/2, p['pad']/2+1.0
        for ang in (45,135,225,315):
            a = math.radians(ang)
            g.draw([(p['x']+r_in*math.cos(a), p['y']+r_in*math.sin(a)),
                    (p['x']+r_out*math.cos(a), p['y']+r_out*math.sin(a))], 0.5)
    for t in tracks:
        if t['layer']=='B':
            g.draw(t['pts'], t['w'])
    for v in vias:
        g.flash(v['x'],v['y'], g.circle(VIA_PAD))
    for v in [v for v in vias if v['net']=='GND']:
        g.polarity('C'); g.flash(v['x'],v['y'], g.circle(VIA_PAD+2*0.55))
        g.polarity('D')
        r_in, r_out = VIA_PAD/2, VIA_PAD/2+0.8
        for ang in (45,135,225,315):
            a = math.radians(ang)
            g.draw([(v['x']+r_in*math.cos(a), v['y']+r_in*math.sin(a)),
                    (v['x']+r_out*math.cos(a), v['y']+r_out*math.sin(a))], 0.4)
    for p in pads:
        if p['net']!='GND':
            g.flash(p['x'],p['y'], g.circle(p['pad']))
    g.save(os.path.join(gdir,'IPQ-CARRIER_V1.GBL'), {'FileFunction':'Copper,L2,Bot'})

    # 阻焊
    for fn, side in (('IPQ-CARRIER_V1.GTS','Top'), ('IPQ-CARRIER_V1.GBS','Bot')):
        g = Gerber()
        for p in pads:
            g.flash(p['x'],p['y'], g.circle(p['pad']+2*MASK_EXP))
        for v in vias:
            g.flash(v['x'],v['y'], g.circle(VIA_PAD+2*MASK_EXP))
        for (mx,my) in npths:
            g.flash(mx,my, g.circle(MH_D+2*0.3))
        g.save(os.path.join(gdir,fn), {'FileFunction':'Soldermask,%s'%side})

    # 丝印：顶层全量；底层仅放预镜像标题（从底面看为正字）
    g = Gerber()
    for (x1,y1,x2,y2,w) in silk_lines:
        g.draw([(x1,y1),(x2,y2)], w)
    for (t,x,y,h,rot) in silk_texts:
        for (a,b,c,d) in text_strokes(t,x,y,h,rot):
            g.draw([(a,b),(c,d)], 0.18)
    g.save(os.path.join(gdir,'IPQ-CARRIER_V1.GTO'), {'FileFunction':'Legend,Top'})

    g = Gerber()
    for (t,x,y,h) in [('IPQ-2026 CARRIER v1.0 BOTTOM', 47.5, 40.0, 1.6)]:
        segs = text_strokes(t, x, y, h)
        xs = [p for s in segs for p in (s[0], s[2])]
        x0, x1m = min(xs), max(xs)
        for (a,b,c,d) in segs:
            g.draw([(x0+x1m-a, b), (x0+x1m-c, d)], 0.18)
    g.save(os.path.join(gdir,'IPQ-CARRIER_V1.GBO'), {'FileFunction':'Legend,Bot'})

    # 板框
    g = Gerber()
    g.draw([(0,0),(BOARD_W,0),(BOARD_W,BOARD_H),(0,BOARD_H),(0,0)], 0.1)
    g.save(os.path.join(gdir,'IPQ-CARRIER_V1.GKO'), {'FileFunction':'Profile'})

    # 钻孔
    ex = Excellon()
    for p in pads:
        ex.add(p['drill'], p['x'], p['y'])
    for v in vias:
        ex.add(VIA_D, v['x'], v['y'])
    ex.save(os.path.join(gdir,'IPQ-CARRIER_V1-PTH.drl'))
    exn = Excellon()
    for (x,y) in npths:
        exn.add(MH_D, x, y)
    exn.save(os.path.join(gdir,'IPQ-CARRIER_V1-NPTH.drl'), plated=False)

    zpath = os.path.join(out, 'IPQ_CARRIER_V1_gerber.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(gdir)):
            z.write(os.path.join(gdir,f), 'IPQ-CARRIER_V1/'+f)
    return out, gdir, zpath

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    errs, warns = run_drc()
    out, gdir, zpath = emit()
    render(os.path.join(out,'preview_top.png'), 'T')
    render(os.path.join(out,'preview_bottom.png'), 'B', mirror=True)
    with open(os.path.join(out,'report.txt'),'w') as f:
        f.write('IPQ CARRIER DRC-lite report\n'+'='*50+'\n')
        f.write('焊盘 %d，过孔 %d，走线段 %d\n\n' % (len(pads), len(vias), sum(len(t['pts'])-1 for t in tracks)))
        if errs:
            f.write('[ERROR] %d 项\n' % len(errs))
            for e in errs: f.write('  '+e+'\n')
        else:
            f.write('[PASS] 无间距/环宽/板边错误\n')
        if warns:
            f.write('\n[WARN]\n')
            for w in warns: f.write('  '+w+'\n')
    print('pads=%d vias=%d tracks=%d' % (len(pads), len(vias), len(tracks)))
    print('DRC errors: %d, warnings: %d' % (len(errs), len(warns)))
    for e in errs[:60]: print('  ERR', e)
    for w in warns[:10]: print('  WARN', w)
    print('output ->', out)
