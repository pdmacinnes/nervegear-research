# Spec: Software-only causal EMG hand-pose benchmark

Status: Software-only scope and continuation approved by the maintainer on October 14, 2026. Dataset audit complete. The audit-derived pilot protocol is documented for implementation review.

Created: October 14, 2026. Revised after the maintainer clarified that specialized hardware will not be available.

The filename is retained to preserve existing links. This proposal replaces the earlier recording-and-tactile-feedback experiment. The starter dataset is downloaded and inspected. No decoder, model training, hardware purchase, or human experiment has started.

The [dataset audit](../docs/datasets/emg2pose.md) found one person, one session, and 15 stages in the starter archive. The [pilot manifest](../research/emg2pose/pilot-v1.json) therefore specifies a custom left-hand regression pilot with recordings 1-9 for training, 10-12 for validation, and 13-15 for testing. This narrows the initial evaluation to held-out stage recordings within a session. It is not the official population-generalization benchmark. No initial reference pose is supplied. Default outputs use all 20 joint angles, with macro per-recording MAE as the primary score.

## Requirements & Goals

Build a reproducible offline benchmark of hand-pose decoding from public surface EMG recordings. The question is whether a simple causal decoder maintains useful accuracy under limited calibration and held-out evaluation, and how prediction quality changes with processing window and simulated signal corruption.

The maintainer has no specialized hardware now and expects no future access. Every acceptance criterion must be achievable on an ordinary computer. Do not require electrodes, a headset, implants, new recordings, participant recruitment, lab access, GPUs, or paid cloud services. The specialized-hardware budget is USD 0.

Start with emg2pose and its author-maintained [dataset documentation](https://github.com/facebookresearch/emg2pose). Audit metadata, licenses, labels, and split definitions before downloading recordings. Use the starter subset for software checks only unless its actual coverage supports a declared scientific comparison. Do not require the full archive. A different dataset requires a documented amendment that identifies compatible labels and changes to the hypothesis.

The first target is hand joint angles using the author's label definitions. Audit coordinate conventions, units, valid masks, and timestamps before fixing the selected joints. Do not invent grasp force or intention labels from kinematics. This dataset records natural movement and cannot establish stationary low-force control.

Use a CPU-compatible baseline, such as regularized regression on past-only EMG features. Include a train-set mean-pose baseline. If a tracking method uses an initial reference pose, declare the initial-pose input and compare against a hold-initial-pose baseline with the same information. Do not let one model use extra reference measurements silently.

The primary metric is mean absolute joint-angle error on a frozen held-out manifest, in declared angular units. Report per-joint and per-subject or per-session results so long recordings do not silently dominate the aggregate. A lower error is a scientific outcome, not a completion condition. A negative result is acceptable.

## Inputs, Outputs & Behavior

Inputs are licensed public EMG recordings, aligned reference joint angles, available source metadata, and a versioned experiment configuration. Use generated synthetic fixtures for tests of alignment, causal processing, splits, and known failure conditions.

Outputs are a dataset card, acquisition manifest, frozen evaluation manifest, preprocessing description, simple baseline results, error and timing tables, robustness plots, and a report. An optional desktop hand-pose replay may aid inspection. It is not required and does not demonstrate embodiment.

The normal flow is:

1. Inventory the ordinary computer's memory, processor, disk, and available software. Do not assume a GPU or install a paid service.
2. Audit metadata and the license. Record the source version or commit, source URLs, file identifiers, available people and sessions, target labels, and official evaluation definitions.
3. Propose a bounded subset. Default download limits are at most 1 GiB of archives and 5 GiB of project data on disk. These are provisional project caps, not claims about actual extraction sizes. Stop and narrow scope if the selected data exceed them.
4. Download only the declared files after the audit. Record checksums and actual sizes. Follow author download methods rather than inventing unsupported per-file endpoints.
5. Validate timestamps, masks, finite values, coordinate conventions, and alignment with synthetic fixtures and data inspection.
6. Freeze train, validation, and test membership by source grouping before windowing. Preserve official held-out identities for any claim of official-benchmark comparability. Treat an original smaller experiment as a separate evaluation.
7. Fit preprocessing and the simple decoder using training data only. Select parameters on validation data. Do not use test outcomes to select the model, window, joints, or calibration policy.
8. Evaluate prediction at time t using samples at or before t. Label window duration, update period, prediction horizon, signal conditioning, and any initial reference pose.
9. Compare declared past-only windows, for example 50, 100, and 200 ms, when the selected data permit them. A causal history window is not automatically an equivalent buffering delay. Report actual buffering or lookahead separately.
10. Measure processing time distributions after warm-up under a declared CPU configuration. Report model execution, feature processing, replay scheduling, and whole-pipeline timing separately where applicable. Do not call offline execution time sensor-to-percept latency.
11. Apply seeded channel dropout, noise, gain changes, and software delay. State their exact definitions. Artificial corruption is not evidence of real electrode replacement or physiological drift.
12. Report paired outcomes on the same test examples and resource use. Publish code, manifests, and acquisition instructions. Do not redistribute recordings or derived data unless their license permits it.

Evaluate held-out people, tasks, and sessions only where metadata and subset membership support them. Separate recording sessions are not necessarily separate calendar days or documented sensor replacements. If a comparison is unsupported, report it as unavailable.

Any calibration experiment must declare its labeled-data allowance, separate calibration examples from scored examples, and give matched methods the same allowance. A model adapted with test labels is a supervised-calibration condition rather than zero-calibration generalization.

No simulated human feedback policy is needed for the first benchmark. A later controller simulation would require a separate spec that states the plant, user-policy assumptions, and what empirical data constrain them. Fixed recording replay is never a live physiological closed loop.

The dataset audit will set a provisional run-time cap for the chosen computer before training. Keep one fully specified CPU run as the reproducibility target. Optional larger models or accelerators must not determine project completion.

## Edge Cases & Error Handling

- If the license is incompatible with intended use, stop acquisition and revise the data choice. Public download access is not a license.
- If a file is unavailable, corrupt, or has a checksum mismatch, record the failure and revise the manifest explicitly. Do not silently substitute data.
- If archive or extracted size exceeds the caps, stop and narrow the subset. Do not fetch the full dataset automatically.
- If the starter subset lacks independent groups, limit it to software checks and identify a bounded supported evaluation. Do not claim generalization from overlapping windows.
- If reference units or timestamps are ambiguous, resolve them before scoring. Do not choose a time shift by minimizing test error.
- If channels or reference joints are invalid, apply a predetermined mask and report exclusions. Do not remove difficult test examples after seeing their errors.
- If preprocessing uses future samples, label it noncausal and keep it out of the causal comparison. Include filter initialization and boundary behavior in the audit.
- If initial pose is unavailable, use a method that does not need it or declare the condition unsupported. Do not infer unseen test reference inputs without disclosure.
- If a channel fails or a stream segment is missing, produce an explicit invalid or degraded output with timestamps. Do not score fabricated predictions as ordinary valid samples.
- If a model fails to outperform mean pose, report the result. Investigate alignment and data leakage without changing frozen expectations to make a model win.
- If a timing target fails, report the bottleneck and measured configuration. Do not remove slow runs from the distribution without a declared rule.
- If rest or intended-action labels are absent, do not report physiological idle detection or false intent activations. Synthetic stale-input handling is a software property only.
- If session dates or electrode-replacement records are absent, do not report cross-day or sensor-replacement validation.
- If a run exceeds the declared compute limit, stop it and document the revised design. Do not add paid compute as an implicit dependency.

## Acceptance Criteria

Scope and readiness:

- [x] The maintainer approves the software-only scope and continuation before implementation. Audit-derived protocol details are recorded in the linked pilot manifest.
- [ ] Every required milestone works without specialized hardware, new recordings, lab access, a GPU, or paid cloud services.
- [ ] A dataset card states source version, license, targets, units, masks, acquisition conditions, supported comparisons, and unsupported claims.
- [ ] A bounded acquisition manifest records checksums and sizes within the declared limits. No full-archive dependency exists.
- [ ] A frozen evaluation manifest defines grouping, train and validation separation, test membership, joint selection, primary metric, and calibration allowances.

Implementation and measurement:

- [ ] Behavior tests fail for expected faults before fixes and pass afterward. Appropriate unit, lint, and execution checks pass before the implementation PR. A user-facing replay, if added, has a journey check and inspected screenshot.
- [ ] Tests prove alignment and that changing future samples cannot change earlier causal predictions or features. They also check train-only normalization and split isolation.
- [ ] The baseline and decoder use matched reference inputs and report initial-pose access explicitly.
- [ ] Missing, invalid, and stale segments produce documented outputs and scoring exclusions, with coverage reported.
- [ ] A repeatable CPU command reproduces the baseline and a small evaluation on public data within the machine-specific run budget.
- [ ] `FEATURE_MAP.md` describes the implemented commands and checks once executable features exist.

Results and interpretation:

- [ ] The report gives held-out angular error, per-group aggregation, scored coverage, window length, prediction horizon, buffering, processing-time distribution, and resource use.
- [ ] Corruption tests use declared seeded parameters and the same test examples as the clean condition.
- [ ] Supported generalization comparisons are reported. Unsupported people, task, session, day, rest, or replacement comparisons are named as unavailable.
- [ ] Results include null or negative findings and do not require beating the baseline to count as complete.
- [ ] Published materials include reproducible configuration and manifests without credentials or restricted recordings.
- [ ] The report explicitly limits conclusions to offline prediction and simulated perturbations. It makes no claim of live physiological control, tactile benefit, subjective perception, full-dive capability, or clinical safety.
