# Research roadmap

Evidence baseline: October 14, 2026. Time windows are research planning horizons, not predictions of full-dive availability.

## Complete the independent work in software

The maintainer has no specialized hardware and expects no future access. Every required milestone must finish on an ordinary computer using public data, analysis, or simulation. Do not make hardware purchases, laboratory access, new recordings, participant recruitment, GPUs, or paid cloud services prerequisites.

The first project asks how hand-pose prediction accuracy and responsiveness change under causal processing and held-out evaluation. The maintainer approved the software-only scope and pilot protocol. The [dataset audit](docs/datasets/emg2pose.md) and [first CPU pilot](docs/experiments/emg2pose-pilot-v1.md) are complete. The simple ridge decoder loses to train-only constant-pose baselines. See [spec 001](specs/001-stationary-virtual-hand.md), the [frozen protocol](research/emg2pose/pilot-v1.json), and the [reproduction guide](docs/reproduce-pilot.md).

The available starter data cover one person in one session. The first pilot therefore uses disjoint stage recordings within that session. It cannot establish new-person, new-session, or actual sensor-replacement performance. Broader data access is not a dependency for completing the pilot.

| Step | Work | Evidence required to finish |
| --- | --- | --- |
| 1. Audit the evidence and data | Check licenses, target labels, official splits, session coverage, and bounded downloads | A dataset card and an evaluation manifest that support the intended claims |
| 2. Review the revised spec | Fix the target, primary metric, comparisons, causality rules, and compute limits | Maintainer approval of the revised scope before implementation |
| 3. Establish a CPU baseline | Use synthetic fixtures and a small public subset to reproduce loading, alignment, and a simple decoder | Passing behavior tests, a repeatable command, and measured resource use |
| 4. Run held-out evaluations | Compare accuracy and timing under declared past-only windows and calibration allowances | Paired results against simple baselines on a frozen test manifest |
| 5. Test robustness | Apply reproducible channel dropout, noise, gain changes, and added software delay | Sensitivity curves explicitly labeled as simulated perturbations |
| 6. Publish the benchmark | Release code, manifests, environment details, and results without restricted recordings | A reproducible report that states limitations and includes negative findings |
| 7. Choose the next question | Follow the strongest observed failure or compare a sensory-encoding model | One bounded follow-on hypothesis supported by the benchmark |

Steps 1-6 are complete for the bounded v1 pilot. The next question is why RMS ridge underperforms constant pose. Diagnose training/validation feature shifts and joint-specific residuals before proposing another model. The v1 test outcomes are now known, so future work must disclose that exposure rather than call them an unseen test.

The approved diagnostic command in [spec 002](specs/002-decoder-failure-diagnostics.md) is implemented. The [report](docs/experiments/decoder-diagnostics-v1.md) shows better training fit, loss of validation advantage, substantial recording-specific bias, and agreement between independent solvers. The command opens only training and validation recordings. Tests prove that test files are unnecessary and cannot change its scientific outputs.

The approved [spec 003](specs/003-limited-label-calibration.md) is implemented: nine original-training folds, a fixed 10-second prefix, a 200 ms embargo, and six matched comparisons. The [calibration report](docs/experiments/limited-label-calibration-v1.md) finds no aggregate MAE improvement over uncalibrated ridge or the primary equally informed constant. All nine folds are supported and reported.

The October 14, 2026 session ended after that verified delivery. All five completed PRs are merged into `main`.

The approved October 15 [temporal alignment audit](docs/experiments/temporal-alignment-v1.md) is complete. Aligned ridge scores 17.111 degrees macro MAE versus 18.529 for the mean of the past and future 5-second errors, with seven improved and two worsened folds. All nine folds are supported. Correct timing helps this decoder on aggregate, but the prefix-median constant retains slightly lower MAE at 17.059 degrees on the same targets. Future shifts are diagnostic controls with future access. This result supports temporal information in the fixed decoder without establishing neural latency or live control.

The proposed next experiment is the [causal history study](specs/005-causal-history-decoder.md). Compare the current 200 ms RMS representation, a 600 ms RMS representation, and five recent 200 ms feature windows spanning 600 ms. Retain training-median and prefix-median controls on common timestamps. Fix regularization before results and test that duplicating current features alone cannot weaken it. The specification awaits approval before implementation or real-data analysis. A sensory-encoding simulation remains a separate possible direction.

The existing pilot, diagnostic, calibration, and alignment artifacts remain separate so their different scoring subsets and label access stay explicit. Every further experiment needs its own bounded hypothesis and approved protocol.

Read source metadata before downloading large recordings. The small starter subset checks software; it is not automatically sufficient for subject or session generalization. If the available subset cannot support a claim, narrow that claim. Do not expand automatically to the full archive or rent compute.

Offline replay is a complete research method with limited claims. Predictions cannot change the actions in a fixed recording. It does not establish live user control, stationary movement, tactile benefit, embodiment, or clinical safety. A simulated feedback controller adds model assumptions rather than human evidence.

## Near term: 0-5 years

Approximately 2026-2031.

Independent contributions can include causal decoding benchmarks, reliable evaluation splits, uncertainty estimation, calibration studies, signal compression, and sensitivity to synthetic corruption. Use public datasets and report the original acquisition conditions. Software can also compare tactile encoders or prosthetic-vision models under stated assumptions.

The wider field may improve low-force readout, sensory feedback, and clinical home use. Those external developments inform this project but are not its deliverables. Do not wait for access to implants or recording equipment.

## Medium term: 5-15 years

Approximately 2031-2041.

Possible independent work includes testing methods across new public cohorts, improving model-based sensory encoding, and contributing evaluation tools to established open projects. Cross-dataset work requires compatible labels and permissions. A shared task name alone does not establish comparability.

The wider field needs richer chronic sensory prostheses, selective access, and evidence of useful simultaneous perception. Public evidence from other researchers can update the feasibility study. This repository does not promise to perform those physical experiments.

## Long term: 15+ years

Beyond approximately 2041.

Strict full-dive needs coordinated sensory experience, safe motor separation, management of contradictory natural sensation, and acceptable chronic risk. There is no defensible completion date. These remain research questions even if software models become much better.

The independent path remains complete without hardware access. Reproducible methods, well-controlled negative results, and better comparisons can contribute to the field while leaving physiological validation to appropriately equipped researchers.

## Separate project milestones from field milestones

For this repository, finish a dataset audit, a baseline, a frozen comparison, and a report. Add optional desktop visualizations only when they help inspect the results. Do not build a VR scene merely to make an offline decoder look like a full-dive demonstration.

For the wider field, the sequence remains reliable action control, useful sensory feedback, limb embodiment, simultaneous sensory and motor function, convincing stationary movement, and safe repeated operation. Completing a software benchmark does not complete those physiological milestones.

## Keep costs and publication bounded

The required specialized-hardware budget is USD 0. No paid service is required. Record the ordinary computer's capabilities before setting a data and runtime budget. Prefer a small CPU experiment over a large model that requires an assumed GPU.

Choose a project license before inviting substantial external contributions. Respect dataset licenses separately. Keep downloaded data and generated run files out of Git. Publish acquisition instructions and manifests rather than bundling another project's recordings.
