# Spec: Stationary virtual-hand feasibility experiment

Status: Proposed, awaiting maintainer approval.

Created: October 14, 2026.

This document specifies a possible first experiment. Publishing it does not approve implementation, hardware purchases, recruitment, or human data collection.

## Requirements & Goals

Investigate whether low-force surface electromyography can control one continuous virtual grasp command while the physical hand remains comfortably supported. Test whether sparse mechanical tactile feedback improves control after sensors are removed and replaced across days.

The experiment addresses motor readout, feedback encoding, calibration drift, latency, and the distinction between physical stillness and physiological inactivity. It does not claim natural tactile restoration, complete movement suppression, or full-dive VR.

The primary scientific question is whether informative feedback reduces absolute virtual grasp-force error during a standardized hold task when visual force information is partially obscured. Task success, force overshoot, completion time, workload, and embodiment are secondary outcomes.

Start with a conventional controller and synthetic biosignals to establish task behavior. Add recording hardware only after the task and measurement path work. Begin with two EMG channels and one command dimension. Compare a simple amplitude-based controller with a learned controller only if the simpler controller exposes a concrete limitation.

The physical interface uses recording electrodes and benign mechanical vibration. It excludes implants, electrical nerve stimulation, pain generation, thermal stimulation, and active movement suppression. Maintain an independent user stop control.

The estimated hardware planning allowance is USD 300-1,000 excluding an existing computer and optional headset. Confirm equipment already available and review a current parts list before purchase. A headset is optional for the first task.

## Inputs, Outputs & Behavior

Inputs are two timestamped EMG streams, calibration references, physical movement measurements, a selected task condition, and an independent stop signal. The software baseline accepts conventional input and synthetic streams with known values.

Outputs are one normalized virtual grasp command, virtual object state and force, mechanical feedback commands, and a local session record. The record includes timing, controller configuration, condition order, calibration events, task outcomes, and data-quality events.

The normal flow is:

1. Verify the bench-tested acquisition and feedback paths before body-connected use. Body-connected recording electronics operate on battery power and communicate wirelessly. Do not charge or attach mains-connected acquisition equipment while electrodes are worn.
2. Check skin contact and comfort. Support the hand without restraint that prevents voluntary withdrawal.
3. Record baseline rest, low-force calibration activity, and a physical movement reference. State the movement measurement's accuracy and detection limit.
4. Run a practice block. Freeze task thresholds and analysis choices before collecting the comparative evaluation data.
5. Run randomized blocks under visual-only feedback, informative tactile feedback, and control vibration with similar exposure but no useful relation to the current task.
6. Ask the user to grasp and hold virtual objects without dropping or crushing them. Object stiffness and target force come from a reproducible schedule.
7. Partially obscure visual force information in the evaluation task. Keep the amount of occlusion consistent across conditions.
8. Record rest periods and incidental movement to measure false activations.
9. Include feedback-only relaxed trials to test whether vibration mechanically contaminates the EMG or movement measurements.
10. Repeat across at least five separate days with sensor removal and replacement. Record calibration time and controller changes each day.
11. Analyze the primary outcome by session and condition. Report uncertainty, missing data, and null or negative results.

Use a counterbalanced order across days. Decide the number and length of blocks, trial count, rest intervals, matching of control vibration, and the primary statistical contrast before human evaluation. A one-person pilot is exploratory and cannot establish population-level efficacy.

The data record must distinguish user-generated commands from any assistance the virtual controller provides. Synchronize independent devices and measure residual clock error. Use physical measurements of actuator onset when reporting end-to-end output delay.

For raw EMG, target acquisition near 1-2 kHz per channel when supported by the chosen hardware and antialiasing design. Process signals causally. Record the filter response, window length, update period, and measured controller delay. An envelope-only sensor is sufficient for a basic amplitude controller but does not establish motor-unit decoding.

The provisional engineering target is a 95th-percentile command-to-feedback onset delay of at most 100 ms after the controller emits a command. Report acquisition and estimation delay separately and also report the total signal-to-feedback delay. This is a project target, not a biological full-dive requirement.

The implementation deliverables are a reproducible task, calibration procedure, measurement report, analysis, and a hardware description. Publish synthetic or deliberately approved de-identified data only. Store raw personal recordings outside version control.

## Edge Cases & Error Handling

- If acquisition becomes stale, disconnects, or loses timestamp ordering, enter idle and disable feedback until the operator restarts the session.
- If electrodes detach, the signal clips, or data quality leaves the validated range, pause the trial and label its data. Do not silently interpret the fault as intention.
- If feedback contaminates EMG, identify the path and fix or redesign the setup before interpreting comparative results.
- If a person experiences discomfort, fatigue, skin irritation, or motion sickness, stop the session. A discomfort event is data, not a reason to push through the task.
- If the stop control, application, or feedback device fails, the feedback output must stop independently of the learned controller.
- If the physical movement sensor cannot detect small displacements, report that limit. Do not report that no movement occurred.
- If performance changes after sensor replacement, report both fixed-controller and recalibrated results. Do not combine them into one generalization score.
- If the controller activates during rest, report events per minute and their magnitude. Accuracy during prompted movement cannot replace this measure.
- If data are missing, exclude or retain them under a declared rule and report the affected trials. Do not hide failed sessions.
- If a model uses overlapping windows, split by session before windowing. Fit normalization and other learned preprocessing on training data only.
- If a model uses future samples or another noncausal step, label the analysis offline. Do not report its execution time as live controller latency.
- If synthetic or conventional input succeeds but EMG does not, treat the result as a working task with an unproven physiological interface.

Before recruiting anyone, establish the applicable consent, privacy, and research review requirements. Keep participant identities, consent records, and biosignals out of the public repository. A future publication or dataset release needs a separate release review.

## Acceptance Criteria

Approval and readiness:

- [ ] The maintainer approves this spec and records the decision before implementation.
- [ ] The task, primary contrast, trial schedule, rest schedule, movement threshold, and analysis rules are fixed before comparative human data collection.
- [ ] The parts list fits the approved budget, and the acquisition and feedback paths pass bench checks before body-connected use.
- [ ] Applicable human research, consent, and data-handling requirements are established before recruitment or collection.

Software and measurement:

- [ ] The conventional-input and synthetic-input baseline runs repeatable grasp, hold, drop, and crush scenarios with known ground truth.
- [ ] Behavior tests fail for expected faults before their implementation fixes and pass afterward. Required unit, lint, build, and journey checks pass before a prototype PR.
- [ ] Acquisition failure, stale input, invalid timestamps, and operator stop each produce a verified idle state and disabled feedback.
- [ ] A screenshot of the implemented task is inspected before the UI is considered complete.
- [ ] `FEATURE_MAP.md` describes implemented capabilities and their verification when the prototype exists.
- [ ] The report includes raw acquisition rate, processing windows, controller update rate, clock error, and measured delay distributions.
- [ ] The provisional 100 ms command-to-feedback 95th-percentile target is measured. A miss blocks comparative evaluation until its cause is understood and the design is fixed or the target is explicitly revised.

Experiment and reporting:

- [ ] The system exposes one continuous command and explicit idle detection, with task performance and rest false activations reported.
- [ ] Physical movement, effort, calibration time, and the limits of their measurements are reported.
- [ ] Informative tactile feedback is compared with visual-only feedback and matched control vibration under randomized, counterbalanced conditions.
- [ ] Feedback-only relaxed trials establish whether mechanical artifacts can explain the decoded signal.
- [ ] At least five separate recording days include sensor removal and replacement, with fixed-controller and recalibrated results identified separately.
- [ ] The report includes all completed and failed sessions, primary and secondary outcomes, uncertainty, and any departure from the approved protocol.
- [ ] Reproduction materials contain no credentials, identities, consent documents, or unapproved personal recordings.
- [ ] The report accepts a null result and makes no claim of full-dive capability or population-level efficacy from a one-person feasibility pilot.
