# NerveGear research

A technical research project on safe, non-lethal full-dive virtual reality, grounded in neuroengineering, sensory restoration, and reproducible experiments.

## Current assessment

Useful partial systems are achievable research targets. An integrated system that replaces an awake person's sensory world while allowing natural virtual movement with a stationary body remains beyond demonstrated technology.

Motor and speech readout are ahead of rich sensory writing. Proprioception, balance, safe movement separation, and chronic interfaces are major unresolved problems. A hybrid of sensory-organ, muscle, skin, peripheral, spinal, and brain interfaces deserves function-specific evaluation.

This repository starts with a literature-based study. It contains no implemented full-dive device, experimental software, or completed human experiment. The evidence baseline is **October 14, 2026**. Roadmap dates are planning horizons, not product predictions.

## Read the research

| Document | Contents |
| --- | --- |
| [Feasibility study](docs/feasibility-study.md) | Technical capabilities, human demonstrations, quantitative limits, unresolved problems, and bottleneck ranking |
| [Evidence matrix](docs/evidence-matrix.md) | Capability-by-capability comparison, limitation types, and required advances |
| [Systems architecture](docs/systems-architecture.md) | Components and information flows, including unresolved physical-body interactions |
| [Reading list](docs/references.md) | 54 sources covering papers, programs, datasets, tools, and motivation |
| [Roadmap](ROADMAP.md) | Immediate work and 0-5, 5-15, and 15+ year research horizons |
| [First-project spec](specs/001-stationary-virtual-hand.md) | Proposed stationary virtual-hand experiment using low-force EMG and tactile feedback |

## Start with one measured closed loop

The proposed first project asks whether sparse tactile feedback improves low-force EMG control of a virtual grasp after sensors are removed and replaced across days.

1. Audit the papers behind the experiment and approve its spec.
2. Build the virtual grasp task with conventional input and synthetic signals.
3. Choose and bench-test recording hardware against the measured requirements.
4. Add EMG, idle detection, mechanical feedback, and physical movement measurement.
5. Compare informative feedback with visual-only and control conditions across at least five separate days.
6. Publish a reproducible feasibility report, including null or negative results.

The spec is **proposed and awaiting approval**. Hardware purchases, implementation, recruitment, and data collection have not started. A headset is optional. The planning hardware budget is USD 300-1,000 excluding a computer and optional headset, subject to parts review.

## Read evidence labels precisely

H means demonstrated in humans, A in animals, L a laboratory prototype, and T theoretical. These labels can overlap. A human research prototype is not necessarily a practical product.

Peer-reviewed findings, preprints, institutional announcements, company demonstrations, and program objectives are separate source types. Recording rate, electrode count, task throughput, and perceptual capacity are separate measurements.

Palmer Luckey's NerveGear discussion supplies motivation only. The project concerns the non-lethal sensory and motor interface.

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md) before adding claims, experiments, or data. Use branches and pull requests. Keep automatic merging disabled. Keep personal recordings and credentials out of version control.

A project-wide reuse license has not been selected. Linked papers, datasets, and software retain their own terms.
