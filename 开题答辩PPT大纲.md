# 开题答辩 PPT 大纲与讲稿（7–8 分钟，纯英文）

> 配套文件：`project proposal form - IPQ draft.docx` / `PPF draft answers.md`
> **成品幻灯片：`IPQ开题答辩.pptx`（12 页，16:9）**——本大纲即其逐页内容与讲稿。
> 用法：每页给出【幻灯片上放什么】（英文要点）和【讲什么】（英文讲稿，含时长）。
> 讲稿全文约 1150 词 ≈ 7 分半（140 词/分钟）。幻灯片只放要点，句子留给嘴说。
> 待替换项：第 1 页 `[Your Name]`；第 3、9 页的图片占位框（小车照片、CSV 曲线截图）。

## 总览

| # | 幻灯片 | 部分 | 时长 |
|---|--------|------|------|
| 1 | Title | — | 0:20 |
| 2 | Outline | — | 0:15 |
| 3 | The Problem I Met | 1 背景与动机 | 0:50 |
| 4 | Two Ways to Command a Motor | 1 背景与动机 | 1:00 |
| 5 | Research Gap & Research Question | 1 背景与动机 | 0:45 |
| 6 | Test Platform & Measurement | 2 实验设计 | 0:45 |
| 7 | Variables & Experimental Protocol | 2 实验设计 | 1:00 |
| 8 | Metrics & Hypotheses | 2 实验设计 | 0:45 |
| 9 | Feasibility: Platform & Data Pipeline | 3 可行性 | 0:40 |
| 10 | Feasibility: Skills, Risks & Backups | 3 可行性 | 0:40 |
| 11 | Timeline (Aug 2026 – Apr 2027) | 4 时间规划 | 0:45 |
| 12 | Summary & Expected Contribution | — | 0:30 |

**合计 ≈ 7:35**（留 20–30 秒缓冲）

---

## Slide 1 — Title（0:20）

**幻灯片内容：**
- S-curve vs. PID: Energy, Time and Differential Suppression for a Two-Motor Robot Car
- 一行小字放研究问题缩写版：*Which control strategy moves my robot car faster and cheaper — and which one keeps it straight?*
- Name / Centre CN213 Shanghai Guanghua College / IPQ 06/27 / Date

**讲稿：**
> Good afternoon everyone. My IPQ project compares two classic ways of controlling robot motors — S-curve motion profiling and PID feedback — on a robot car I built myself. I will measure which one completes a movement using less energy and less time, and which one can keep the car driving straight. Let me start with why I chose this topic.

## Slide 2 — Outline（0:15）

**幻灯片内容：**
- 1 Background & Motivation
- 2 Experimental Design
- 3 Feasibility
- 4 Timeline

**讲稿：**
> My presentation has four parts: the background and motivation, the experimental design, the feasibility, and my timeline from now until submission next April.

## Slide 3 — The Problem I Met（0:50）

**幻灯片内容：**
- Built a two-motor robot car (ESP32 + encoder motors)
- Observation 1: motors = biggest power consumer → battery drains fast, much energy wasted
- Observation 2: same PWM ⇒ two wheels differ by ~5% in speed → car drifts off a straight line
- Question raised: does *how* we command the motors change energy cost and accuracy?

**视觉建议：** 小车照片 + 两张遥测截图（rpmL vs rpmR 曲线分叉的那段）

**讲稿：**
> My interest came from building and testing this car. The first thing I noticed is that the motors are by far the biggest power consumers on the car — they drain the battery quickly, and a lot of the energy seems wasted rather than turned into motion. The second observation is on this plot: when both motors receive exactly the same PWM command, the two wheels still run at different speeds — about five percent apart, measured by the wheel encoders. That five percent comes from small manufacturing differences between the two motors, and it makes the car slowly curve off a straight line. So I started asking: does the way we command the motors change how much energy a movement costs, and how accurately the car moves?

## Slide 4 — Two Ways to Command a Motor（1:00）

**幻灯片内容：**
- S-curve motion profiling (open loop)
  - Speed follows a smooth, jerk-limited S-shaped reference
  - Standard in CNC / industrial robots; limits vibration & stress
  - (Nguyen et al. 2008; Meckl et al. 1998)
- PID feedback control (closed loop)
  - Controller corrects PWM continuously from measured speed error
  - Most widely used control algorithm in industry
  - (Åström & Hägglund; Mahmud et al. 2020; Hammoodi et al. 2020)
- Key structural difference: **open loop sees nothing; closed loop corrects**

**视觉建议：** 左右对比框图：左边 S 曲线→PWM→电机（无回箭头），右边编码器→PID→PWM→电机（有反馈回路）

**讲稿：**
> In the literature there are two mainstream answers to "how should a robot command its motors". The first is S-curve motion profiling. The speed reference follows a smooth, S-shaped curve that limits jerk. This is the standard in CNC machines and industrial robots, because it reduces vibration and mechanical stress. The second is PID feedback control, the most widely used control algorithm in industry: the controller reads the actual wheel speed from the encoders and continuously corrects the motor input to reduce the error. The structural difference is crucial: an S-curve profile is open-loop — however beautifully it is planned, it cannot see what the motors actually do. PID is closed-loop — it measures and corrects. In theory, feedback should be able to cancel the five-percent mismatch between my two motors, and no open-loop profile can.

## Slide 5 — Research Gap & Research Question（0:45）

**幻灯片内容：**
- Gap: most comparisons are **simulation-based, single idealised motor**
  - no mismatched-motor problem, no battery, no energy data
- Open questions on real, low-cost hardware:
  1. Which strategy completes a speed-change task with **less energy**?
  2. Which is **faster** to settle at the target speed?
  3. How much can **only PID** suppress the wheel-speed differential?
- **Research question** (highlight box):
  *How do S-curve open-loop profiling and PID closed-loop control compare in electrical energy and task time on a two-motor robot car, and to what extent can PID additionally suppress the wheel-speed difference that open-loop control cannot solve?*

**讲稿：**
> Here is the gap. Almost all the comparisons I found are simulations with a single idealised motor. In simulation the two motors are perfectly matched and power is free, so neither of my real problems exists. On real, battery-powered hardware, three questions stay open: which strategy uses less energy, which one settles faster, and how much wheel-speed differential can feedback alone remove? That gives my research question: I will compare S-curve and PID on the same car in energy and time, and quantify the differential suppression that only PID can provide.

## Slide 6 — Test Platform & Measurement（0:45）

**幻灯片内容：**
- ESP32 + 2 × JGB37-520B encoder motors (330 counts/rev) + DRV8833 driver
- Sensors: INA226 (voltage / current / power) · MPU6050 gyroscope (yaw rate)
- Firmware (already running): dual-wheel PID @100 ms, anti-windup, optional feed-forward
- Telemetry logged at 10 Hz to CSV: target, rpmL, rpmR, PWM, gyrZ, V, I, P
- To add: on-board **S-curve reference generator** for the open-loop mode

**视觉建议：** 平台框图或实物接线图 + CSV 列名截图

**讲稿：**
> This is my test platform, already built and working. An ESP32 controls two geared DC motors with encoders through a motor driver. Two sensing systems make the comparison measurable: an INA226 power sensor samples the electrical voltage, current and power, and a gyroscope measures the car's yaw rate — an independent check of whether the car is turning. The firmware already implements dual-wheel PID with anti-windup, and logs every variable — target speed, both wheel speeds, PWM, yaw rate, voltage, current, power — at ten hertz to a CSV file. The one thing I still need to add is an on-board S-curve reference generator, so the same car can run both strategies.

## Slide 7 — Variables & Experimental Protocol（1:00）

**幻灯片内容：**
- Independent variable: control strategy (S-curve open-loop vs. tuned PID)
- Dependent variables: **energy per task (J) · settling time (s)** · wheel-speed difference (rpmL−rpmR) · yaw rate
- Controlled: same car, surface, battery voltage window, target speeds, routine; ≥3 repeats per condition
- Experiments:
  - **A** Same speed-change task under both strategies → energy & time
  - **B** Step response → dynamics
  - **C** One-factor-at-a-time PID tuning (Kp, Ki, Kd, FF) → fair tuning
  - **D** Identical S-curve commands vs. per-wheel PID → differential suppression
  - **E** Robustness across target speeds (15 / 45 / 90 rpm)
- Extension: PID tracking an S-curve reference (combined strategy)

**讲稿：**
> The design is a controlled experiment. The independent variable is the control strategy. The main dependent variables are energy per movement and settling time, plus the wheel-speed difference and yaw rate. Everything else is controlled: the same car, the same surface, the same battery voltage window, and each condition is repeated at least three times. Five experiments: A runs the identical speed-change task under both strategies and compares energy and time. B measures the step response. C tunes the PID gains one factor at a time — this is important for fairness, so PID is properly tuned, not misrepresented. D is the unique-capability test: identical S-curve commands to both wheels versus independent PID on each wheel, measuring how much feedback removes the differential. E repeats the comparison at different target speeds. If time allows, I will also test a combined strategy: PID tracking an S-curve reference — the best of both worlds.

## Slide 8 — Metrics & Hypotheses（0:45）

**幻灯片内容：**
- Energy: integrate measured power over task time, E = Σ P·Δt (INA226 @10 Hz)
- Settling time: from command until speed stays within ±5% of target
- Analysis: mean ± SD over ≥3 repeats, plots in Python/Excel
- Hypotheses:
  - H1: PID settles **faster** but may overshoot; S-curve is smooth by construction
  - H2: energy outcome is genuinely **open** — that is why it must be measured
  - H3: PID drives rpmL−rpmR → ~0; open-loop S-curve leaves ~5% → drift

**讲稿：**
> How do I judge the winner? Energy is the time integral of the measured electrical power. Settling time runs from the command until the wheel speed stays within a five-percent band of the target. Three hypotheses. First, PID should settle faster, because an S-curve deliberately stretches the acceleration, but PID may overshoot. Second — and this is the honest part — I do not know which one uses less energy; that is exactly why the experiment is worth doing. Third, PID should push the wheel-speed difference close to zero, while the open-loop S-curve leaves the five-percent difference and the car keeps drifting. Any result here is informative.

## Slide 9 — Feasibility: Platform & Data Pipeline（0:40）

**幻灯片内容：**
- Hardware: **built, wired and running** — wiring checklist v3.3 tested
- Firmware: PID, telemetry, CSV logging **already produce data** (sample on the right)
- Remaining build work: one S-curve generator function (weeks, not months)
- Low cost, common components → easy to repair / replace
- Supervisor support for experimental design

**视觉建议：** 一张已经跑出来的 CSV 曲线截图（证明数据管线可用）

**讲稿：**
> Is this feasible? The car is already built and wired, following a tested wiring checklist. The firmware already produces exactly the kind of data I need — this plot on the right came out of a real test run last week. The only engineering work left is one S-curve generator function, which is a matter of weeks, not months. All components are cheap and common, so anything that breaks can be replaced quickly, and my supervisor reviews the experimental design with me.

## Slide 10 — Feasibility: Skills, Risks & Backups（0:40）

**幻灯片内容：**
- Skills in hand: Arduino/ESP32 programming · Python data logging (pyserial, pandas) · PID theory from Åström & Hägglund
- Risk → Mitigation:
  - INA226 sensor drops out → auto-reconnect in firmware + multimeter cross-check
  - Battery voltage drifts → fixed voltage window per session + voltage logging
  - Quantisation noise at short sampling → 100 ms period, low-pass filter, 3+ repeats
  - Schedule slip → 6-week buffer before submission
- Ethics & safety: low voltage (≤9 V), bench-tested, wheels off ground first

**讲稿：**
> On skills: I already write the firmware, the Python logger and the analysis myself, and the PID theory is covered by the literature. Key risks and my mitigations: if the power sensor drops out, the firmware reconnects automatically and I can cross-check with a multimeter. If the battery voltage drifts, I test within a fixed voltage window and log voltage with every sample. Encoder noise is handled by the 100-millisecond sampling period, a low-pass filter and repeated trials. And the timeline carries a six-week buffer. Safety is simple: everything runs below nine volts, and new behaviours are always bench-tested with the wheels off the ground first.

## Slide 11 — Timeline（0:45）

**幻灯片内容（表格或甘特图）：**

| Phase | Time | Deliverable |
|---|---|---|
| S-curve generator + pilot tests | Aug–mid Sep 2026 | tested open-loop mode |
| Main experiments A–E + repeats | mid Sep–Nov 2026 | complete CSV dataset |
| Extension (combined strategy) | Nov–Dec 2026 | extra dataset |
| Data analysis + literature write-up | Dec 2026–Jan 2027 | figures, draft review section |
| Report writing | Jan–Feb 2027 | first full draft |
| Revision + supervisor review | Mar 2027 | second draft |
| Buffer + proofreading + submission | Apr 2027 | final report (06/27 series) |

**讲稿：**
> Here is my plan from now to submission. By mid-September I will finish the S-curve generator and pilot tests. The main experiments with repeats run through November, and December gives room for the combined-strategy extension. January is for analysis and the literature write-up, February and March for drafting and revising the report with my supervisor's feedback, and April is buffer, proofreading and submission. Every phase ends with a concrete deliverable, so slippage is visible early.

## Slide 12 — Summary & Expected Contribution（0:30）

**幻灯片内容：**
- Same car, same task, two strategies — measured, not assumed
- Outcomes: energy vs. time trade-off **+** quantified differential suppression
- Deliverable: evidence-based guidance for battery-powered robots; open dataset
- Thank you — Questions?

**讲稿：**
> To summarise: on one car, under identical conditions, I will measure — not assume — the energy and time trade-off between S-curve planning and PID feedback, and quantify the one thing only feedback can do: keeping two mismatched motors running at the same speed. The result is evidence-based guidance for anyone building battery-powered robots. Thank you — I am happy to take questions.

---

## 讲述小贴士

- 数字要说得出处：5% 差速、10 Hz、100 ms、330 counts/rev、±5% 稳定带——都来自你的真实系统，被追问时用 Slide 6/8 的数据回答。
- 全场只讲一个故事：“我造了车 → 车有两个毛病（耗电、跑偏）→ 两种经典方案各管一半 → 我用同一辆车量化谁换来什么”。
- 时间控制：Slide 7 最容易超时，超了就砍 C（调参）的展开描述，只念加粗部分。
