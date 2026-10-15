# NerveGear research

A technical research project on safe, non-lethal full-dive virtual reality, grounded in neuroengineering, sensory restoration, and reproducible experiments.

## Current assessment

Useful partial systems are achievable research targets. An integrated system that replaces an awake person's sensory world while allowing natural virtual movement with a stationary body remains beyond demonstrated technology.

Motor and speech readout are ahead of rich sensory writing. Proprioception, balance, safe movement separation, and chronic interfaces are major unresolved problems. A hybrid of sensory-organ, muscle, skin, peripheral, spinal, and brain interfaces deserves function-specific evaluation.

This repository contains a literature-based study and a reproducible CPU-only EMG decoding pilot. It contains no implemented full-dive device or completed human experiment. The evidence baseline is **October 14, 2026**. Roadmap dates are planning horizons, not product predictions.

## Read the research

| Document | Contents |
| --- | --- |
| [Feasibility study](docs/feasibility-study.md) | Technical capabilities, human demonstrations, quantitative limits, unresolved problems, and bottleneck ranking |
| [Evidence matrix](docs/evidence-matrix.md) | Capability-by-capability comparison, limitation types, and required advances |
| [Systems architecture](docs/systems-architecture.md) | Components and information flows, including unresolved physical-body interactions |
| [Reading list](docs/references.md) | 54 sources covering papers, programs, datasets, tools, and motivation |
| [Roadmap](ROADMAP.md) | Immediate work and 0-5, 5-15, and 15+ year research horizons |
| [First-project spec](specs/001-stationary-virtual-hand.md) | Approved software-only benchmark of causal hand-pose decoding from public EMG recordings |
| [Dataset audit](docs/datasets/emg2pose.md) | Verified starter data, license, labels, quality checks, and a bounded one-person pilot |
| [Pilot results](docs/experiments/emg2pose-pilot-v1.md) | A simple decoder loses to constant pose; accuracy, sensitivity, timing, and limits |
| [Failure diagnostics](docs/experiments/decoder-diagnostics-v1.md) | Training fit improves, validation advantage disappears, and numerical checks agree |
| [Calibration study](docs/experiments/limited-label-calibration-v1.md) | A fixed labeled prefix does not improve aggregate MAE over uncalibrated ridge or the primary matched-label constant |
| [Reproduction guide](docs/reproduce-pilot.md) | Install, acquire the bounded data, run the experiment, and verify the package |
| [Feature map](FEATURE_MAP.md) | Executable behavior and its tests |

## Start with public recordings and a causal decoder

The project assumes no access to specialized hardware now or later. Every required milestone must be achievable on an ordinary computer using public data, analysis, or simulation. A headset, electrodes, implants, new recordings, lab access, a GPU, and paid cloud services are not prerequisites.

The first project asks how prediction accuracy and responsiveness change when a hand-pose decoder can use only past and current EMG samples. Test generalization on held-out people, tasks, and recording sessions only where the chosen subset permits those comparisons.

1. Audit the dataset, license, labels, split definitions, and download requirements.
2. Review the revised software-only spec before implementation.
3. Build a small CPU baseline with synthetic fixtures and a bounded public-data subset.
4. Measure held-out pose error, causal window length, processing time, and failure under missing or noisy input.
5. Compare a simple decoder against a matched baseline and publish the results, including null or negative findings.

The approved first pilot is complete. The validation-selected RMS ridge decoder scores 22.110 degrees of test macro angular error, compared with 13.957 degrees for a train-set median pose. All three declared histories lose to constant-pose baselines. Five CPU runs reproduce the same scientific results. Read the [report](docs/experiments/emg2pose-pilot-v1.md) before interpreting those numbers.

The [follow-on diagnostics](docs/experiments/decoder-diagnostics-v1.md) are complete using only training and validation data. Ridge improves training fit but loses its advantage on validation tasks. Independent solvers agree, while rare range violations and simple feature shifts leave much of the failure unexplained.

The [fixed-prefix calibration study](docs/experiments/limited-label-calibration-v1.md) is also complete. Using only original training recordings, 10-second intercept calibration scores 17.103 degrees macro error versus 16.886 for uncalibrated ridge and 16.217 for the primary equally informed prefix-median constant. All nine folds are reported. Calibration helps some recordings but does not improve the declared aggregate comparison.

The proposed [temporal alignment audit](specs/004-temporal-alignment-audit.md) compares correctly timed predictions with fixed time shifts within the same held-out recording. It asks whether this decoder benefits from movement timing before changing models. The specification awaits approval. No implementation or new analysis has started.

The data contain one person in one session, so this work cannot establish new-person or new-session performance. No later hardware stage is required. Offline decoding and simulated perturbations cannot establish live user control, tactile benefit, subjective perception, or clinical safety.

## Read evidence labels precisely

H means demonstrated in humans, A in animals, L a laboratory prototype, and T theoretical. These labels can overlap. A human research prototype is not necessarily a practical product.

Peer-reviewed findings, preprints, institutional announcements, company demonstrations, and program objectives are separate source types. Recording rate, electrode count, task throughput, and perceptual capacity are separate measurements.

Palmer Luckey's NerveGear discussion supplies motivation only. The project concerns the non-lethal sensory and motor interface.

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md) before adding claims, experiments, or data. Use branches and pull requests. Keep automatic merging disabled. Keep personal recordings and credentials out of version control.

A project-wide reuse license has not been selected. Linked papers, datasets, and software retain their own terms.
