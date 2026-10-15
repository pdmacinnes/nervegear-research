# Spec: Diagnose the RMS ridge failure on training and validation data

## Requirements & Goals

Status: Specification explicitly approved by the maintainer on October 14, 2026 through the spec-review prompt. It extends the [completed v1 pilot](001-stationary-virtual-hand.md) and preserves its [frozen protocol](../research/emg2pose/pilot-v1.json) and [negative results](../docs/experiments/emg2pose-pilot-v1.md).

Build one reproducible diagnostic command and report to investigate why the simple EMG decoder loses to constant pose. Use the nine training and three validation recordings already acquired. Do not open the three test recordings. Their v1 outcomes are already known and cannot become a fresh blind evaluation.

Distinguish four possible explanations with descriptive evidence:

1. Errors persist on training data, consistent with limitations of the fitted features, model, or objective.
2. Validation features or target poses differ from training distributions.
3. Predictions extend outside the training pose range and contribute large errors.
4. Numerical conditioning or solver disagreement undermines the fitted solution.

These explanations can overlap. Observational diagnostics cannot establish a unique biological or causal explanation. An inconclusive report completes the study. Do not require the model to improve.

The maintainer has no specialized hardware and expects no future access. Complete this work on an ordinary CPU computer with the existing data and dependencies. Require no new download, GPU, paid service, lab access, electrodes, headset, implants, participants, or recordings. Preserve the existing two-thread and 15-minute command limits. This study does not implement new features, models, calibration, clipping, time shifts, or hyperparameter selection.

## Inputs, Outputs & Behavior

Inputs are the existing v1 protocol and the 12 training and validation HDF5 files. Reuse the audited loader, trailing RMS features, validity masks, common warm-up, output cadence, standardization, and ridge objective. Retain 50, 100, and 200 ms histories and alphas 0.1, 1, and 10. The v1-selected 200 ms, alpha-10 model remains the primary diagnostic example. Report all nine declared configurations as sensitivity analysis, without selecting a replacement.

Add `python -m nervegear_benchmark diagnose --data-dir <directory> --output <new-directory>`. Retain the existing `--manifest` option. Existing `run` behavior and the frozen v1 artifacts remain unchanged.

Produce a new run directory containing aggregate `summary.json`, the diagnostic configuration and its fingerprint, a completion marker, a Markdown report, and static SVG plots. Publish a reviewed report and aggregate artifacts in the repository. Do not publish raw signal samples, per-sample target poses, residuals, predictions, or copied upstream code. Report joint indices in the audited target order and group results by recording and stage. Preserve dataset attribution and source-license links.

The normal flow is:

1. Validate protocol metadata and select the nine training and three validation entries before checking recording existence, size, hashes, or contents. Read no test recording. Record the actual 12-file input inventory and checksums in the output. Fingerprint parsed protocol JSON independently of indentation and line endings.
2. Load each selected recording with the existing path-containment, checksum, and schema checks. Build common eligible output timestamps. Report candidate, invalid-input, invalid-reference, and scored counts for every recording. Use identical eligible timestamps for paired model and baseline comparisons.
3. Fit the same train-only mean pose, median pose, and nine ridge configurations. Do not pool validation data into fitting or normalization. Compute training and validation results separately. Reproducing an existing validation error is a consistency check, not new held-out evidence.
4. For each model and recording, report angular MAE, mean squared error, root mean squared error, and per-joint MAE. Report equal-recording macro MAE and sample-weighted MAE separately. Define macro MSE as the mean of per-recording MSE and macro RMSE as its square root. Include train and validation scores so good in-sample fit cannot be confused with good transfer.
5. For the primary model, decompose each recording's per-joint residual MSE into squared residual mean plus population residual variance. Use prediction minus reference as the residual. Verify the identity numerically. Summarize bias magnitude without treating the terms as causal contributions.
6. Describe each recording's reference-pose mean, standard deviation, interquartile range, and MAE around its own per-joint median. That last value is the best possible constant-pose MAE for that recording with access to its labels. Label it a descriptive within-recording lower bound for constant predictors. It is unavailable to a deployed decoder and is excluded from model selection and fair baseline comparisons.
7. Describe feature shift relative to the training standardization for each history. Report training feature means and scales, constant-feature flags, and training 1st/99th percentiles. For every training and validation recording, report channel-wise standardized feature means, standard deviations, fractions with absolute standardized value greater than three, and fractions outside the training 1st/99th percentile interval. These are descriptive thresholds, without a normality assumption or population-level significance claim.
8. For the primary model, report per-joint fractions of predictions and reference targets outside the training target minimum/maximum and outside its 1st/99th percentile interval. Report errors for inside-range and outside-range prediction groups where they exist. Do not clip predictions or interpret training ranges as physiological joint limits.
9. Report singular values, numerical rank, and condition number of the standardized training feature matrix for each history. For each declared alpha, report the condition number of the regularized system and coefficient norm. Independently solve the augmented least-squares system and compare predictions with the existing ridge solution. This checks numerical consistency without changing the fitted model.
10. Measure whole-command wall time, CPU time, and peak process memory. Treat these as resource checks on an interactive desktop, not speedup claims or physiological latency. Write a completion marker only after all required artifacts are successfully generated. Refuse an existing output directory.
11. Write a report that distinguishes measured observations, interpretations, and unresolved alternatives. Compare the evidence across recordings and joints rather than highlighting only favorable rows. Declare one bounded follow-on hypothesis based on these diagnostics. A new model experiment requires a separate protocol that discloses previous test exposure.

Use ordinary descriptive statistics only. Overlapping windows and temporally correlated samples are not independent biological replicates. Do not report population confidence intervals, significance from window counts, or new-user, new-session, cross-day, clinical, perception, or full-dive conclusions.

## Edge Cases & Error Handling

- Missing test recordings do not cause failure because the command never accesses them. Missing training or validation recordings fail explicitly. Do not silently substitute or skip recordings.
- Corrupt files, unsafe paths, unsupported protocol changes, or schema mismatches fail before publishing completed results. Retain the existing resource and file boundaries.
- A recording with no eligible scored outputs fails with its filename and exclusion counts. Do not omit a difficult recording from the aggregate.
- A constant training feature uses the existing unit scale and carries an explicit constant-feature flag. A validation deviation in that channel remains visible rather than being divided by zero or dropped.
- A rank-deficient unregularized matrix reports its rank and a null condition number with an explicit singular flag. Do not serialize Infinity or NaN. The positive ridge penalties must still yield a finite regularized solution.
- An empty inside-range or outside-range group reports a count of zero and null group error. Empty groups cannot appear to have perfect accuracy.
- If independent solvers disagree beyond relative tolerance 1e-7 and absolute tolerance 1e-9 for predictions, fail verification and investigate. Do not publish a causal interpretation from an unverified solution.
- If a statistic or score unexpectedly becomes nonfinite, fail explicitly. Do not replace it with zero. Document any rounding used only for display.
- If the command exceeds 15 minutes or fails to write an artifact, do not leave a successful completion marker. No paid compute or larger model is an automatic fallback.
- If all proposed diagnostics are inconclusive, report that limitation and select a discriminating next question. Do not add post-hoc tests of the known v1 test recordings.

## Acceptance Criteria

- [x] The maintainer confirms this specification before implementation code is written.
- [x] The diagnostic command succeeds with only the 12 training and validation recordings present; its verified loaded-file inventory contains no test recording.
- [x] Synthetic end-to-end tests fail for expected missing behavior before implementation, then pass. They cover test-file absence, train-only statistics, paired masks, bad hashes, missing required files, singular features, empty subgroups, and refusal to overwrite outputs.
- [x] Synthetic known-answer tests verify macro versus sample weighting, the residual MSE decomposition, the within-recording constant-pose lower bound, feature shift, range-exclusion counts, and independent solver agreement.
- [x] The report contains training and validation scores for all nine fixed ridge configurations and both fair constant-pose baselines, with no replacement-model selection.
- [x] The primary model's validation scores reproduce the frozen v1 validation result within numerical tolerance. Frozen v1 protocol and results remain byte-for-byte unchanged.
- [x] Coverage, per-recording and per-joint errors, target dispersion, feature shifts, prediction ranges, conditioning, and independent solver checks are recorded with units and definitions.
- [x] A complete CPU run finishes within the existing resource limits without additional data, specialized hardware, GPU, or paid services.
- [x] The report states what is supported, what remains inconclusive, the known test exposure, and one bounded next hypothesis. It makes no physiological or population-generalization claim.
- [x] Documentation and `FEATURE_MAP.md` describe the new command. Meaningful tests, lint, formatting, package builds, an installed-package smoke check, link checks, and Linux/Windows CI pass before delivery. Inspect generated plots.
- [x] Only code, documentation, configuration, aggregate metrics, and plots are published through a branch and PR with automatic merging disabled. Data and per-sample outputs remain excluded.
