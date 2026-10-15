# Research roadmap

Evidence baseline: October 14, 2026. Time windows are research planning horizons, not predictions of full-dive availability.

## Complete the independent work in software

The maintainer has no specialized hardware and expects no future access. Every required milestone must finish on an ordinary computer using public data, analysis, or simulation. Do not make hardware purchases, laboratory access, new recordings, participant recruitment, GPUs, or paid cloud services prerequisites.

The first project asks how hand-pose prediction accuracy and responsiveness change under causal processing and held-out evaluation. The maintainer approved the software-only scope and continuation. The [dataset audit](docs/datasets/emg2pose.md) is complete. The starter archive is downloaded and inspected, with no model training yet. See [spec 001](specs/001-stationary-virtual-hand.md) and the [pilot proposal](research/emg2pose/pilot-v1.json).

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
