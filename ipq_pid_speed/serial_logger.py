#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口记录器 —— 配合 ipq_pid_speed 固件的 'e' 命令（串口 CSV 输出）使用，
没有 SD 卡时用它把实验数据直接记录到电脑。

用法：
    py serial_logger.py            # 列出串口，按提示选择
    py serial_logger.py COM5       # 直接指定端口

依赖（只需装一次）：
    pip install pyserial

操作流程：
    1. 先关掉 Arduino IDE 的串口监视器（同一端口只能被一个程序打开）；
    2. 运行本脚本；
    3. 在串口里发命令（本脚本也能发：直接键盘输入回车，如 w / x / o / kp3.0）；
    4. Ctrl+C 结束，得到两个文件：
       pid_log_时间戳.csv  ← 纯数据行，可直接 Excel/pandas 分析
       pid_log_时间戳.txt  ← 完整串口记录（含命令回显，备查）
"""
import sys
import re
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("缺少 pyserial，请先运行:  pip install pyserial")

CSV_RE = re.compile(r"^\d+,-?[\d.]")          # 数据行特征：以毫秒数开头


def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        ports = list(list_ports.comports())
        if not ports:
            sys.exit("未发现串口设备，请确认 ESP32 已通过 USB 连接")
        for i, p in enumerate(ports):
            print(f"[{i}] {p.device}  {p.description}")
        port = ports[int(input("选择端口序号: "))].device

    try:
        ser = serial.Serial(port, 115200, timeout=1)
    except serial.SerialException as e:
        sys.exit(f"打开 {port} 失败：{e}\n（若提示拒绝访问，请先关闭 Arduino IDE 的串口监视器）")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    txt = open(f"pid_log_{stamp}.txt", "w", encoding="utf-8")
    csv = open(f"pid_log_{stamp}.csv", "w", encoding="utf-8", newline="")
    print(f"已连接 {port} @115200 → pid_log_{stamp}.csv / .txt")
    print("键盘输入命令回车即发送（如 w / x / o / kp3.0 / e），Ctrl+C 结束记录\n")

    import threading
    stop = threading.Event()

    def sender():                              # 后台线程：键盘 → 串口
        while not stop.is_set():
            try:
                line = input()
                if line:
                    ser.write((line + "\n").encode())
            except EOFError:
                return

    threading.Thread(target=sender, daemon=True).start()

    wrote_header = False
    try:
        while True:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if not line:
                continue
            txt.write(line + "\n")
            txt.flush()
            if CSV_RE.match(line):
                if not wrote_header:
                    csv.write("ms,tgt,rpmL,rpmR,pwmL,pwmR,gyrZ,busV,curA,powW\n")
                    wrote_header = True
                csv.write(line + "\n")
                csv.flush()
            print(line)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        ser.close()
        txt.close()
        csv.close()
        print(f"\n记录完成：pid_log_{stamp}.csv / pid_log_{stamp}.txt")


if __name__ == "__main__":
    main()
