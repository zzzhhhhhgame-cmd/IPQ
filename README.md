# IPQ 项目仓库

**研究课题**：在自建双电机小车上，对比 S 曲线开环运动规划与 PID 闭环控制在**电能消耗**、**任务时间**上的差异，并量化 PID 反馈对**双轮转速差**（直线跑偏）的抑制能力——这是开环控制无法解决的问题。

**硬件平台**：ESP32 DevKit V1 + DRV8833 电机驱动 + JGB37-520B 编码器电机 ×2 + INA226 电压/电流传感器 + IMU（MPU6050 / LSM6DS3 自动识别）+ microSD 模块。

---

## 目录结构

```
IPQ/
├── 工程文件/          # 小车工程：代码、接线、物料清单
│   ├── ipq_robot_test/        # 全系统联合测试程序（.ino + 操作说明）
│   ├── ipq_pid_speed/         # 双轮 PID 速度控制程序（.ino + 教程/说明 + 串口日志）
│   ├── i2c_identify/          # I2C 器件识别小工具（确认 IMU 实际芯片型号）
│   ├── wiring.html            # 接线总图（网页版）
│   ├── wiring-checklist.html  # 逐线接线检查清单（v3.1，与固件引脚一一对应）
│   └── bom.html               # 物料清单（BOM）
│
├── 答辩/              # 项目申请书（Project Proposal Form）及答案草稿
│   ├── PPF draft answers.md              # PPF 各栏目的答案草稿（Markdown，便于复制修改）
│   ├── project proposal form - IPQ draft.docx  # 申请书 Word 草稿（与上一文件内容一致）
│   └── project proposal form(1).docx           # 申请书 Word 版本
│
├── 参考资料/          # 整理性资料：硬件资料、教材、论文总结、实验提取报告及其生成脚本
│   ├── D2-1-2F（未焊接）/               # DRV8833 驱动板产品资料（接线说明、引脚图、真值表、芯片手册、uno 示例代码）
│   ├── PID Controllers (Åström & Hägglund).pdf  # PID 控制经典教材（理论背景）
│   ├── summaries/                    # 5 篇论文的中文总结 PDF（自整理）
│   ├── extracted/                    # 5 篇论文的全文纯文本提取（工作数据）
│   ├── Experiment_Extraction_Report.pdf  # 5 篇论文的实验设计提取报告（自整理）
│   ├── gen_summaries.py              # 生成 summaries/ 的脚本（ReportLab）
│   ├── gen_experiments.py            # 生成 Experiment_Extraction_Report.pdf 的脚本
│   └── _exp_content.py               # 提取报告的正文数据（被 gen_experiments.py 加载）
│
├── 参考文献/          # 研究引用的原始文献
│   └── paper/         # 5 篇原始论文 PDF（括号内为对应总结编号）
│       ├── Control-BLDC-Motor-Speed-using-PID-Controller.pdf            # Mahmud et al., 2020（01）
│       ├── Design_and_implementation_speed_control.pdf                 # Hammoodi et al., 2020（02）
│       ├── FA01_1.pdf                                                  # Meckl et al., 1998（03）
│       ├── Speed_Control_of_DC_Motor_Using_Fuzzy_PI.pdf                # Bansal et al., 2013（04）
│       └── nguyen-et-al-2008-on-algorithms-for-planning-s-curve-motion-profiles.pdf  # Nguyen et al., 2008（05）
│
├── .gitignore
└── .gitattributes
```

---

## 分类说明

### 1. 工程文件（及其说明）

小车本体相关的全部工程内容。三个 Arduino/ESP32 工程：

| 工程 | 用途 |
|---|---|
| `ipq_robot_test` | 全系统联合测试：双电机 + 编码器 + IMU + INA226 + microSD，遥测 10 Hz 记录 |
| `ipq_pid_speed` | 双轮独立 PID 速度控制（含抗积分饱和），附实验教程、使用说明和串口日志（`serial_logger.py` 采集） |
| `i2c_identify` | I2C 总线扫描，识别传感器板上实际焊接的芯片型号 |

接线与物料文档：`wiring*.html` 与 `bom.html`，其中 `wiring-checklist.html` v3.1 与固件引脚定义逐线对应。

### 2. 答辩

IPQ 项目申请书（Project Proposal Form）的填写材料。`PPF draft answers.md` 是各栏目答案的 Markdown 版，便于编辑和复制；两份 `.docx` 为提交用的 Word 版本。**待填写**：Candidate number（大考 4 位考号）、Candidate name（护照拼音名）。

### 3. 参考资料

围绕文献与硬件做的整理性材料：

- **硬件资料**（`D2-1-2F（未焊接）/`）：所用 DRV8833 驱动板的产品资料（接线说明、引脚图、真值表、芯片手册、uno 示例代码）。
- **教材**：Åström & Hägglund《PID Controllers》，PID 整定理论的背景阅读。
- **论文总结**（`summaries/`）：5 篇核心文献的中文总结 PDF。
- **实验提取报告**（`Experiment_Extraction_Report.pdf`）：从 5 篇论文中提取的自变量/因变量/控制变量等实验设计要素，用于设计自己的实验方案。
- **生成脚本**：`gen_summaries.py` 与 `gen_experiments.py`（加载 `_exp_content.py`）可用 ReportLab 重新生成上述 PDF；`extracted/` 为论文纯文本提取结果。

### 4. 参考文献

研究引用的 5 篇原始论文（`paper/`），编号与 `参考资料/summaries/` 一一对应。申请书中引用的完整文献还包括 Åström & Hägglund 教材（见 `参考资料/`）。

---

## 文档再生成方法

两个生成脚本已改为相对路径，可在任意系统上运行（依赖 `reportlab`；中文字体自动在 Windows / macOS 系统字体中查找，也可将 Noto Sans SC 字体放在脚本同目录）：

```bash
cd 参考资料
pip install reportlab
python gen_summaries.py     # 重新生成 summaries/ 下 5 份总结 PDF
python gen_experiments.py   # 重新生成 Experiment_Extraction_Report.pdf
```

## 工作约定

- 修改任何文件后提交并推送到 `origin/main`。
