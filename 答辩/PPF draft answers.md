# IPQ Project Proposal Form — 答案草稿

> 与 `project proposal form - IPQ draft.docx` 内容一致，方便复制修改。
> 修改后如需同步回 Word，直接替换对应表格里的文字即可。
> 待你自己填写：Candidate number（大考 4 位考号）、Candidate name（护照拼音名）。

## Research question

How do S-curve open-loop motion profiling and PID closed-loop control compare in terms of the electrical energy consumed and the time taken to complete a speed-change task on a self-built two-motor robot car, and to what extent can PID control additionally suppress the wheel-speed difference between the two motors — a problem that open-loop control cannot solve?

## Briefly explain why you have chosen this question and topic

My interest in this topic began when I was building and testing my own two-motor robot car. I noticed that the motors were by far the biggest power consumers on the car: they drained the battery quickly, and a large part of the electrical energy appeared to be wasted rather than converted into useful motion. This made me ask whether the way the motors are commanded could change how much energy a movement costs. A second observation followed: when both motors received the same PWM command, the two nominally identical wheels ran at measurably different speeds (about 5% apart, shown by the wheel encoders), so the car drifted off a straight line.

In the literature there are two mainstream answers to "how should a robot command its motors". One is S-curve motion profiling: the speed reference follows a smooth, jerk-limited S-shaped curve, the standard approach in CNC machines and industrial robots because it limits vibration and mechanical stress (Nguyen et al., 2008; Meckl et al., 1998). The other is PID feedback control, the most widely used control algorithm in industry, which continuously corrects the motor input based on the measured speed error (Åström & Hägglund; Mahmud et al., 2020; Hammoodi et al., 2020).

However, most published comparisons are simulation-based and assume a single, idealised motor. On real low-cost hardware the two "identical" motors are not identical, and everything runs on a battery, so two practical questions remain open: which strategy completes a movement using less energy and less time, and which one can handle the motor mismatch that makes my car veer off course? An S-curve profile is open-loop: however well it is planned, it cannot see or correct the speed difference between the two wheels. PID feedback, in principle, can — and quantifying this difference in capability is exactly what I want to do.

The answer has practical value for battery-powered mobile robots and for student robotics projects: if one strategy saves energy and time while the other uniquely guarantees straight-line tracking, choosing between them (or combining them) becomes an evidence-based engineering decision. The project also develops my skills in control engineering, embedded programming and experimental data analysis, which I plan to study further at university.

## Outline the research method(s) you will use and explain how this will help you to answer your research question

**Basic assumptions.** (1) The speed difference between the two motors under identical PWM commands (about 5%) is stable and repeatable, so it can be treated as a systematic error that feedback can cancel. (2) An S-curve speed profile can be generated on board the ESP32 and applied to both motors as a time-varying open-loop PWM reference, while PID uses the encoder-measured wheel speeds as feedback — so both strategies can be tested on the same car under identical conditions. (3) Energy per task, taken as the time integral of electrical power measured by the INA226 sensor, and task time, taken as the time from the command until the wheel speed settles within a fixed band of the target, are fair and valid indicators for comparing the two strategies.

**Research method.** A quantitative controlled-experiment design. Independent variable: control strategy (S-curve open-loop profile vs. tuned PID feedback). Dependent variables: electrical energy per movement (J), task/settling time (s), steady-state speed error, wheel-speed difference (rpmL − rpmR) and yaw rate (gyrZ, an independent measure of the car turning). Controlled variables: the same car, surface, battery voltage range, target speeds and test routine. Each condition is repeated at least three times and analysed with means, standard deviations and plots (Excel / Python). A dedicated experiment then tests the unique capability: identical S-curve commands sent to both wheels vs. independent PID control of each wheel, measuring how much feedback reduces the speed difference and the straight-line drift.

**Technical route.** (1) Literature review of PID tuning theory and S-curve planning algorithms, from which the evaluation metrics and a fair test protocol are derived. (2) Platform: my existing robot car — ESP32 controller, two JGB37-520B encoder motors, DRV8833 driver, INA226 voltage/current sensor and MPU6050/LSM6 gyroscope — whose firmware already implements dual-wheel PID with anti-windup and logs all telemetry (target, wheel speeds, PWM, yaw rate, voltage, current, power) at 10 Hz to CSV; I will add an S-curve reference generator for the open-loop mode. (3) Experiments: A — the same speed-change task under S-curve vs. PID, comparing energy and time; B — step-response measurement; C — one-factor-at-a-time PID gain tuning (Kp, Ki, Kd, feed-forward); D — the differential-suppression test; E — robustness checks at several target speeds. (4) Data analysis and conclusions; if time allows, testing a PID loop that tracks an S-curve reference as a combined strategy.

**How this helps answer the research question.** Experiments A and E provide the direct energy and time comparison; B and C ensure the PID side is fairly tuned rather than misrepresented; D quantifies the wheel-speed suppression that only feedback can provide. Repeated trials and statistical analysis show how reliable each conclusion is.

**Resources required.** The robot-car platform and instruments above (already built and working); a laptop with the Arduino IDE (ESP32 toolchain) and Python (pyserial for data logging, pandas/matplotlib for analysis); batteries and a multimeter; the literature and datasheets listed below; and my supervisor's advice on experimental design.

## Outline the main sources of information you have identified for the project

**Academic literature:**

1. Åström, K. J. & Hägglund, T. — *PID Controllers: Theory, Design and Tuning* (ISA). Foundational PID theory and tuning rules.
2. Mahmud, M., Motakabber, S. M. A., Alam, A. H. M. Z. & Nordin, A. N. (2020). "Control BLDC Motor Speed using PID Controller", *International Journal of Advanced Computer Science and Applications* 11(3). PID speed-controller design.
3. Hammoodi, S. J., Flayyih, K. S. & Hamad, A. R. (2020). "Design and implementation speed control system of DC Motor based on PID control and Matlab Simulink", *International Journal of Power Electronics and Drive Systems* 11(1). PID implementation for DC motors.
4. Bansal, U. K. & Narvey, R. (2013). "Speed Control of DC Motor Using Fuzzy PID Controller", *Advances in Electronic and Electric Engineering* 3(9). Advanced PID variants, for context on the limits of classical PID.
5. Nguyen, K. D., Ng, T.-C. & Chen, I.-M. (2008). "On Algorithms for Planning S-curve Motion Profiles", *International Journal of Advanced Robotic Systems* 5(1). General algorithms for S-curve trajectory planning.
6. Meckl, P. H., Arestides, P. B. & Woods, M. C. (1998). "Optimized S-Curve Motion Profiles for Minimum Residual Vibration". Optimising S-curve profiles to reduce vibration — the classic argument for S-curve motion.

**Databases and search tools:** Google Scholar, IEEE Xplore, ScienceDirect and ResearchGate, searched with keywords such as "S-curve motion profile", "PID DC motor speed control" and "differential drive control".

**Technical documentation and open-source resources:** the Espressif ESP32 Arduino core documentation (GitHub), the Texas Instruments INA226 and DRV8833 datasheets (power measurement and motor driving), the InvenSense MPU6050 / ST LSM6 sensor documents, and open-source PID code such as Brett Beauregard's Arduino PID library as implementation references.

**Primary data:** telemetry CSV logs recorded from the car itself (target speed, both wheel speeds, PWM, yaw rate, voltage, current and power at 10 Hz) — the main evidence base of the project.
