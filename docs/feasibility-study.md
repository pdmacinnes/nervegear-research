# Technical feasibility of safe full-dive virtual reality

Evidence baseline: October 14, 2026.

## Assessment

A useful research path toward partial full-dive VR exists. A safe system that replaces an awake person's sensory world while allowing natural virtual movement with a stationary body remains beyond demonstrated technology.

Motor and speech readout have become useful in humans. Rich sensory writing, natural bodily sensation, and safe separation of virtual movement from physical movement remain less developed. Rendering and raw computing power are unlikely to be the hardest limits of a strict full-dive system.

The most plausible architecture is a hybrid. Use sensory organs for vision and hearing, muscles for accessible motor readout, skin for selected feedback, and peripheral or central neural interfaces where a specific requirement justifies them. A single implant is not a complete architecture.

This document is a focused technical review, not a systematic review or a claim that a complete system is feasible. It preserves distinctions between demonstrated functions and proposed combinations. Palmer Luckey's NerveGear discussion supplies the motivation only. It supplies no evidence of a working full-dive interface. [R47](references.md#r47)

The project is at the research stage. No prototype, experiment, or safety validation has been completed in this repository.

## Define the target

| Target | Meaning | Evidence status |
| --- | --- | --- |
| Rich immersive VR | Vision, sound, tracking, and selected bodily feedback produce presence | Existing systems, with substantial limitations |
| Stationary embodied VR | A largely stationary user controls an avatar through small movements, muscle activity, or neural activity and receives coordinated feedback | Components and limited combinations demonstrated |
| Strict full-dive | A conscious user experiences convincing virtual perception and natural virtual movement while incompatible physical movement and sensory feedback are managed safely | No integrated demonstration identified |

A strict system needs voluntary intent readout, coordinated sensory generation, management of conflicting natural input, safe management of physical movement, stable embodiment, chronic usability, and reliable exit. Full sensory replacement would also include smell, taste, breathing, and visceral sensation.

The evidence labels in this project are:

- **H:** demonstrated in humans.
- **A:** demonstrated in animals.
- **L:** a laboratory or research prototype.
- **T:** theoretical or proposed.

Labels overlap. H-L is a human research prototype, not a consumer device. The source type is a separate property. A company announcement, peer-reviewed experiment, preprint, and program objective provide different kinds of evidence.

## Interpret bandwidth and resolution

Recording rate, useful task throughput, independent neural access, and perceptual capacity are different quantities.

An illustrative 1,000-channel recorder with 30,000 samples per second and 12-bit samples produces 360 Mbit/s before overhead. That arithmetic describes electronics. It does not establish 360 Mbit/s of communication with a person.

Electrode count is not the number of independent percepts. Electrode pitch is not perceptual resolution. A stimulation pulse rate is not a perceptual refresh rate. Decoder execution time excludes other acquisition, estimation, communication, and output delays.

A visual EEG study explicitly distinguished externally encoded information transmitted through visual responses from voluntarily generated command throughput. That distinction matters when comparing headline bit rates. [R06](references.md#r06)

No experimentally established electrode count, neuron count, or bit-rate requirement exists for convincing full-dive. The useful requirement is task dependent. Measurements below are selected demonstrations rather than universal performance ceilings.

## Read neural and neuromuscular signals

| Interface | Human capability | Spatial and temporal interpretation | Main limit and needed advance |
| --- | --- | --- | --- |
| Surface EMG | Gesture, handwriting, and hand-pose inference | Fast muscle electrical signals; useful selectivity depends on muscles, geometry, and decomposition | Physiology, instrumentation, and computation. Remain reliable across placement, posture, fatigue, and sweat |
| Scalp EEG | Selection, motor imagery, limited robotic control | Millisecond measurements, often much longer decision windows; substantial spatial mixing | Physics and computation. Extract more reliable independent control signals |
| MEG | Research decoding of language-related and other activity | Fast electromagnetic recording; source resolution depends on anatomy and models | Instrumentation and physics. Practical operation outside controlled facilities |
| fMRI | Reconstruction of aspects of semantic content | Spatially informative but indirect, slow hemodynamic signals | Biology and instrumentation. Poor fit for portable fast motor control |
| ECoG | Speech, gesture, cursor, and avatar-related output | Local population measurements; dense sampling does not isolate every neuron | Coverage, surgery, and computation. Stable concurrent control across useful regions |
| Intracortical arrays | High-performance speech and multidimensional motor control | Action-potential-scale measurements; useful commands need population decoding | Biology, materials, and surgery. Scalable chronic access with acceptable risk |
| Peripheral nerve and implanted muscle interfaces | Prosthetic control and selected motor-unit access | Fast signals; anatomy and interface placement determine selectivity | Anatomy and materials. Preserve function while obtaining chronic selective access |

Human intracortical evidence now extends beyond short demonstrations. A 2026 study reported more than 3,800 hours of home use by one person using speech and cursor decoders. Personal communication averaged 56 words per minute. Prompted word accuracy reached 99.2%, whereas personal-use utterances were completely correct before correction 53.3% of the time. These metrics use different units and conditions. The system still required care-partner setup and research equipment. [R01](references.md#r01)

A 2025 intracortical study decoded four continuous degrees of freedom from intended finger movements and used them to control a virtual quadcopter. This establishes useful independent control, not a complete hand or whole-body interface. [R02](references.md#r02)

Meta's 2025 wrist EMG work used 2 kHz recording and training across thousands of people. Median results included 20.9 words per minute for handwriting and 0.66 target acquisitions per second for navigation. EMG reads downstream motor activity and remains a strong practical route when motor pathways work. [R03](references.md#r03)

A 2025 EEG robotic-hand experiment classified two or three imagined finger actions online in selected BCI responders. Trials and feedback operated over seconds. It does not establish fast continuous full-body control. [R04](references.md#r04)

Non-invasive semantic reconstruction under trained experimental conditions does not establish unrestricted decoding of arbitrary thoughts. [R05](references.md#r05)

The needed breakthrough is stable concurrent decoding across actions, with reliable idle detection, limited calibration, and useful performance across months and years.

## Write information into the nervous system

A decoder estimates an action or stimulus from measured activity. A sensory encoder must choose stimulation that causes a desired experience in the current neural state. The encoder is a causal control problem, not the automatic inverse of the decoder.

| Method | Evidence | Interpretation | Main gap |
| --- | --- | --- | --- |
| Ordinary sensory stimulation | H; mature displays and audio, H-L richer haptics | Uses native sensory encoding | Arbitrary bodily motion and force in a stationary person |
| Peripheral electrical stimulation | H-L; localized touch and selected movement-related sensations | Fast activation with possible spread across fibers | Independent natural sensory recruitment |
| Spinal stimulation | H-L; motor assistance and selected referred sensations | Organized access to roots and spinal circuits | Fine sensory selection without unwanted motor effects |
| Surface cortical stimulation | H-L; visual and somatic percepts | Population activation with network effects | Rich, predictable combinations of percepts |
| Intracortical microstimulation | H-L; touch, some proprioceptive percepts, phosphenes | Dense access does not guarantee independent percepts | Selectivity, coverage, encoding, and chronic safety |
| TMS and transcranial electrical stimulation | H; modulation and selected evoked phenomena | Broad activation relative to cellular circuits | High-dimensional sensory content writing |
| Focused ultrasound | H-L; targeted modulation | A millimeter-scale acoustic focus is not a sensory pixel | Reliable content, mechanisms, independent channels, and exposure limits |
| Optogenetics | H-L in retinal restoration; broader A-L results | Biological modification plus optical access | Delivery, expression, light access, durability, and translation |

A 2025 human ultrasound system reported an estimated in situ focus of about 1.5 by 1.5 by 2.2 mm at minus 3 dB. This is an acoustic field measurement, not an independently addressable visual or tactile percept. [R25](references.md#r25)

Multifocal holographic ultrasound produced patterned neural activation in mice. Preserve the A-L label when discussing that result. [R26](references.md#r26)

Temporal interference has reached human experiments, including hippocampal modulation. It has not established an arbitrary high-bandwidth sensory interface. [R27](references.md#r27)

The needed breakthrough is reproducible control over independent perceptual dimensions that combine correctly during active behavior. Smaller physical foci alone do not establish this.

## Vision

For a person with functioning eyes, optical displays currently provide a much stronger route than direct artificial vision. They use working retinal circuitry.

In a blind human participant, a 96-channel intracortical array produced phosphenes and distinguishable patterns. Some sites 400 micrometers apart produced distinct percepts, but simultaneous stimulation frequently merged percepts. Physical spacing did not define an ordinary pixel grid. [R13](references.md#r13)

Dynamic cortical stimulation enabled recognition of traced forms, with up to 86 forms per minute in a reported task. This is form recognition throughput, not a video frame rate. [R14](references.md#r14)

A 1,024-electrode visual prosthesis supported shape-related discrimination in monkeys. It is A-L evidence and does not establish the same subjective experience in humans. [R15](references.md#r15)

Illinois Tech reported implantation of 544 electrodes in a third ICVP participant in May 2026. This institutional announcement does not establish 544 independent visual pixels or natural scene vision. [R48](references.md#r48)

Retinal restoration provides another route. The PRIMA study implanted 38 people. Of 32 assessed at 12 months, 26 met its defined clinically meaningful acuity improvement. These restorative results include surgical risks and do not represent normal vision. [R16](references.md#r16)

The main limits are neural encoding, anatomy, stimulation interactions, coverage, and chronic interfaces. Eye movements, cortical magnification, color, depth, and adaptation complicate the mapping. The breakthrough for direct vision is dense coherent perception over a useful field. For healthy users, optical display research remains the practical path. Compact holographic displays are an example of active research on that path. [R51](references.md#r51)

## Hearing

Cochlear implants provide the strongest established clinical example of useful sensory information supplied through electrical stimulation. Speech understanding can be good while pitch, timbre, speech in noise, and localization remain limited.

Contact count is not independent spectral-channel count. Current spread, electrode placement, neural survival, task difficulty, and the individual listener affect usable channels. Classic task results sometimes plateaued around four to eight channels. Newer work shows that this is not a universal fixed ceiling. [R53](references.md#r53)

Rapid electrical pulses do not restore all auditory temporal fine structure. The principal limits are biology, anatomy, and encoding. More selective stimulation that preserves spectral and temporal detail would be a substantial advance. Recent optical cochlear work remains animal evidence for the relevant new capabilities. [R54](references.md#r54)

For healthy hearing, ordinary headphones and spatial audio are the default architecture. Direct neural audio writing is unnecessary for the first milestones.

## Touch

A human bidirectional BCI study showed that adding cortical tactile feedback improved robotic arm control. This establishes a functional benefit from closing the sensory loop. [R07](references.md#r07)

Patterned cortical stimulation later produced edge-like sensations, tactile shapes, and apparent skin motion. Interpretation of motion depended on stimulation duration over tens to hundreds of milliseconds. [R08](references.md#r08)

Spatial coverage is still irregular. One multi-participant study found a median perceived hand-region area of 2.5 square centimeters for individual electrodes, with substantial variation. Multielectrode patterns improved localization and intensity discrimination. [R09](references.md#r09)

Peripheral stimulation also supports useful tactile feedback. Biomimetic temporal patterns improved naturalness and function in human prosthesis experiments. The accompanying animal physiological work answers a separate question. [R10](references.md#r10)

The main limits are selective access, encoding, body coverage, and mechanics. Pressure, slip, texture, vibration, stretch, and contact force require different information. The breakthrough is independent, natural simultaneous sensation across useful body regions. A few vibration actuators can convey task information now, but that is sensory substitution rather than complete tactile reproduction.

## Proprioception and kinesthesia

Position, movement, load, and effort involve muscle and tendon signals, skin and joint input, and central motor predictions. Avatar joint angles do not by themselves produce a matching bodily experience.

Human intracortical stimulation has evoked repeatable movement and position-related sensations. The repertoire remains narrower than natural proprioception. [R11](references.md#r11)

Vibration of reinnervated muscles has produced illusory prosthetic-hand movement and improved control. This is useful peripheral evidence, but it does not establish arbitrary control of an intact person's whole-body position sense. [R12](references.md#r12)

No validated general whole-body angular resolution or perceptual bandwidth exists for an artificial proprioceptive interface. The main limits are sensory biology, system identification, and selective access. The needed breakthrough is continuous control of perceived position, velocity, load, and effort despite contradictory physical input.

## Vestibular sensation and balance

A stationary body does not supply the vestibular signals associated with visually simulated acceleration. Rotation, translation, gravity, eye stabilization, and posture interact.

An eight-person human study used an implant that stimulated three semicircular canal nerve branches. Posture, gait, and quality-of-life measures generally improved. Hearing declined in the implanted ear in all but one participant. Three branches do not represent a complete replacement for bilateral canal and otolith information. [R17](references.md#r17)

Human VR experiments also investigate galvanic vestibular stimulation. Broad perturbation or modulation is different from independent replacement of natural balance signals. [R18](references.md#r18)

There is no demonstrated general six-degree-of-freedom vestibular display with validated natural perceptual resolution. The main limits are biology, anatomy, selectivity, and safety. A major advance would coordinate rotation and gravito-inertial sensations without unwanted eye movements, postural responses, or persistent adaptation.

## Temperature

Physical thermal stimulation at selected residual-limb sites can produce thermal sensations referred to a phantom hand. Wearable thermoelectric systems have supported object-temperature discrimination in humans. This uses peripheral sensory machinery rather than arbitrary brain-based temperature writing. [R19](references.md#r19)

Thermal inertia, contact, skin physiology, actuator size, and heat transfer govern perceptual dynamics. A sensor sampling rate is not thermal perceptual bandwidth. No general neural temperature-display specification is established.

The main limits are thermal engineering, physiology, energy, and safe operating ranges. Distributed, fast, comfortable cues would advance practical VR. A complete neural bypass is less established than physical thermal feedback.

## Pain

Nociceptive signaling, unpleasantness, salience, and conscious pain are related but different. Intracranial stimulation can evoke varied somatic sensations, including temperature-related or unpleasant percepts at some sites. That is not a validated high-resolution pain display. [R20](references.md#r20)

No useful general pain-bandwidth or spatial-rendering specification has been established. The main limits are distributed biology, individual variability, and safety. Predictable quality without damage, sensitization, or persistent effects would be required for a controlled interface.

The initial architecture represents virtual damage through benign tactile, visual, or auditory signals. Deliberate pain generation is outside the proposed first project.

## Other senses

Human VR prototypes have used wearable odor generators. They stimulate sensory organs without a brain implant. Odor clearing, switching, contamination, and adaptation remain important constraints. [R50](references.md#r50)

Taste, oral texture, breathing, heartbeat, and visceral sensation expand the strict replacement problem further. No unified system covers them. Useful intermediate VR can leave these functions natural if its claims state that scope.

## Motor intention and movement suppression

Small movements and low-force isometric contractions provide accessible control with little displacement. They still produce muscle activity, effort, and natural sensory feedback.

Motor imagery can support control without task-sized movement. The limitations include training, variable response, available dimensions, and false activation. Active interruption of motor output is a different proposal.

Clinical BCIs often decode intention after disease or injury has already interrupted movement. They do not demonstrate a safe way to impose that interruption on a healthy person.

High-frequency nerve block has human clinical evidence in post-amputation pain treatment. It does not establish safe recreational whole-body paralysis. [R21](references.md#r21) Animal and modeling studies continue to investigate onset excitation and block behavior. A 2025 rat-nerve study demonstrated onset-free block under particular conditions. [R22](references.md#r22)

A full motor-separation system would need to preserve respiration, swallowing, protective responses, and emergency recovery. It would also need usable intent readout and replacement sensory feedback.

The principal limits are physiology, anatomy, and safety. The required breakthrough is selective, verified reversibility with a safe failure state. Induced paralysis is not a prerequisite for early stationary-interface research.

## Encoding and decoding

A useful conceptual model has a hidden neural and bodily state, artificial stimulation, ordinary sensory input, context, and noisy measurements. The decoder estimates intended actions from measurements. The encoder chooses interventions to create percepts.

The same stimulation may have different effects during rest, movement, attention, or adaptation. A successful decoder does not prove causal control over the corresponding experience.

A 2026 human ECoG study found that models trained on isolated speech and gesture did not fully generalize to simultaneous attempts. Concurrent training improved decoding. A system that reads two behaviors separately has not necessarily solved reading both together. [R52](references.md#r52)

The main limits are neuroscience, causal identification, and computation. The breakthrough is closed-loop models that generalize across context and time, report uncertainty, and handle unfamiliar states without uncontrolled output.

## Latency and bandwidth engineering

The artificial loop includes acquisition and estimation windows, signal processing, decoding, simulation, encoding, communication, and actuation. Neural conduction and perceptual integration add further dynamics.

| Loop | Initial engineering consideration |
| --- | --- |
| Head movement to image | Minimize delay. About 20 ms is a common VR design target, not a universal threshold |
| Contact to tactile cue | Aim for low tens of milliseconds where feasible, then measure jitter |
| Continuous EMG control | Explore roughly 50-150 ms total controller delay as a design range, not a demonstrated sensory requirement |
| Mechanical force servo | Hundreds of hertz to around 1 kHz may be needed for mechanical stability, depending on the device |
| Thermal feedback | Actuator and skin dynamics strongly constrain useful changes |

VR latency effects depend on which component is delayed. [R49](references.md#r49)

The 2025 streaming ECoG speech system generated output in 80 ms increments, while its median go-cue-to-synthesized-speech onset was 1.67 seconds for one test set. These measure different stages. [R28](references.md#r28)

Another intracortical system synthesized voice samples within 10 ms of neural measurements, with additional output delay. This is an engineering achievement, not a universal intention-to-perception latency. [R29](references.md#r29)

For strict full-dive, no validated aggregate bit-rate requirement exists. The practical limits are reliable information extraction, independent sensory control, and synchronization. The needed advance is low-jitter operation across senses under artifacts, dropouts, and changing neural state.

## Chronic safety and adaptation

Non-lethal operation is a weaker requirement than acceptable repeated recreational use. Surgical, vascular, tissue, stimulation, motor, perceptual, software, privacy, and security failures all matter.

A BrainGate safety report covered 14 people and more than 17,000 person-array implant-days. It included procedure- or device-related adverse events and postoperative seizures in two participants, while reporting no device-related death or permanent increase in disability during the one-year evaluation. These results do not establish healthy-user safety for dense multisensory stimulation. [R32](references.md#r32)

Both tissue interfaces and neural representations can change. Materials, encapsulation, corrosion, micromotion, heat, power, telemetry, and removal matter alongside signal quality. The breakthrough is chronic reliability and safety for the combined system, including verified recovery from faults.

Neuroplasticity can support learning and recovery, but also changes the system being controlled. A person and an adaptive decoder can each respond to the other's changes.

Human tactile mapping has tracked percept locations across two to seven years. Spatial stability does not establish unrestricted continuous-stimulation safety. [R09](references.md#r09)

Unsupervised cursor recalibration has been evaluated online over a month in a human participant. Longer retrospective and simulated analyses are separate evidence. [R30](references.md#r30) A 2026 hybrid brain-body neuroprosthesis reported functional and persistent changes in one participant. [R31](references.md#r31)

The main adaptation limits are biology and control. A useful advance would distinguish beneficial learning from recording drift while preserving agency and ordinary function outside VR.

## Choose an interface by function

Direct brain access is not logically necessary for every component. Vision and hearing already use sensory organs effectively. Skin, muscles, peripheral nerves, and spinal pathways provide other access points.

| Location | Functions | Advantage | Constraint |
| --- | --- | --- | --- |
| Sensory organs | Vision, hearing, smell, selected taste | Preserve native encoding | Limited control over bodily contradictions |
| Skin and musculoskeletal system | Touch, force cues, stretch, selected movement illusions | Accessible and reversible | Mechanical forces and body geometry |
| Muscles | Motor readout and selected kinesthetic feedback | Amplify motor commands | Muscle activation or remaining pathways |
| Peripheral nerves | Localized readout and sensory writing | Existing sensory pathways | Mixed fibers, selectivity, and chronic access |
| Spinal roots and cord | Limb sensation and motor circuit access | Organized body pathways | Broad recruitment and reflex interactions |
| Brain | Intent and perception access around damaged pathways | Bypasses downstream injury | Surgery, encoding, coverage, and chronic safety |

In three lower-limb amputees, spinal stimulation evoked sensations referred to a missing foot and supported improvements in balance or gait measures. [R23](references.md#r23) A brain-spine interface restored useful walking control in another human demonstration. Its goal was physical movement, not movement suppression. [R24](references.md#r24)

Peripheral access does not automatically resolve conflict between virtual and real sensation. Direct neural access may ultimately be needed for some strict requirements, but current evidence does not identify a sufficient level or architecture.

## Compare invasiveness

Non-invasive systems offer reversible access and practical independent research. Scalp neural measurements and stimulation face weak signals, spatial mixing, or limited selectivity. Muscle and sensory-organ interfaces avoid some of those limits for their particular functions.

Minimally invasive systems can improve access while reducing some surgical exposure. They still involve biological intervention. Endovascular implants remain implants, surface arrays still require intracranial placement, and external optical control can require gene delivery.

Precision's 2025 study combined a 1,024-channel surface array, delivery work in pigs and cadavers, and an intraoperative five-person human pilot. These are distinct results. They are not a completed chronic human full-dive product. [R33](references.md#r33)

Invasive arrays provide the strongest present local neural readout and direct-writing evidence. They also bring surgery, tissue response, packaging, maintenance, and removal constraints. Each architecture needs function-specific comparison rather than a blanket ranking by invasiveness.

## Company and program evidence

| Organization | Relevant contribution | Evidence boundary |
| --- | --- | --- |
| Neuralink | Implanted wireless motor BCI and assistive-device demonstrations | January 2026 company update reported 21 participants. It does not establish rich sensory writing. [R34](references.md#r34) |
| Synchron | Endovascular recording and digital selection | SWITCH reported four people, with eye tracking plus neural clicking or scanning selection. [R35](references.md#r35) |
| Paradromics | Dense intracortical readout for speech and computer control | First Connect-One chronic study implantation announced in June 2026. Implantation is not mature long-term performance. [R36](references.md#r36) |
| Precision Neuroscience | Conformable dense surface recording | Array clearance up to 30 days is not approval for a permanent full-dive device. [R37](references.md#r37) |
| Meta and CTRL-labs | Scalable wrist EMG input and datasets | Motor input does not establish sensory writing or movement suppression. [R03](references.md#r03) |
| DARPA N3 | Nonsurgical bidirectional interface research | Sixteen channels and 50 ms were objectives, not achieved human specifications. [R38](references.md#r38) |
| DARPA NESD | High-resolution sensory-interface research | Reading one million neurons and writing 100,000 were objectives, not established human capabilities. [R39](references.md#r39) |
| DARPA HAPTIX and RE-NET | Peripheral sensorimotor interfaces and longevity | Relevant precedent for distributed interfaces. Program claims need tracing to individual outcomes. [R40](references.md#r40), [R41](references.md#r41) |

## Rank the bottlenecks

This is a qualitative project assessment for strict full-dive, not a measured consensus. Difficulty uses a scale of 1 to 5. Optical displays, voluntary stillness, and tactile substitution change the ranking for intermediate systems.

| Rank | Bottleneck | Difficulty | Importance | Dominant limit |
| --- | --- | --- | --- | --- |
| 1 | Natural high-dimensional sensory writing | 5 | Critical | Encoding and selective access |
| 2 | Proprioception, load, and effort during physical stillness | 5 | Critical | Distributed biology and conflicting input |
| 3 | Safe separation of virtual and physical movement | 5 | Critical | Physiology, anatomy, reversibility |
| 4 | Chronic interface safety and reliability | 5 | Critical | Materials, tissue, surgery, packaging |
| 5 | Coordinated vestibular and bodily sensation | 5 | Critical | Integration and selective stimulation |
| 6 | Dense direct artificial vision if optical displays are excluded | 5 | Critical for that architecture | Encoding, coverage, interactions |
| 7 | Simultaneous whole-body intent decoding | 4 | High | Access, context, training |
| 8 | Stable adaptation over sessions and years | 4 | High | Drift and adaptive control |
| 9 | Synchronization and artifact rejection | 3 | High | Systems engineering |
| 10 | World rendering and simulation | 2-3 | Necessary, usually not limiting | Compute and software |

## Independent research directions

1. Measure low-force EMG control after sensor replacement across days. Record physical movement, effort, false activations, and calibration burden.
2. Compare sparse tactile encodings for contact, slip, and force. Measure task benefit rather than preference alone.
3. Study decoder adaptation that can detect its own errors rather than reinforce them. Public data can support initial work.
4. Use biomimetic sensory models to test which information a task actually needs. Simulation results remain hypotheses about perception.
5. Evaluate prosthetic-vision encoders under realistic phosphene distortion, dropout, and eye movement. Do not substitute an ordinary low-resolution screen for the interface being modeled.

Public entry points include [emg2pose](references.md#r42), [emg2qwerty](references.md#r43), [TouchSim](references.md#r44), [pulse2percept](references.md#r45), and the [Neural Latents Benchmark](references.md#r46). Check each resource's license and species before using its data.

The recommended first experiment combines low-force motor readout with sparse tactile feedback in a supported virtual-hand task. It tests a real closed loop without an implant. See the [proposed spec](../specs/001-stationary-virtual-hand.md), [roadmap](../ROADMAP.md), [evidence matrix](evidence-matrix.md), [systems diagram](systems-architecture.md), and [reading list](references.md).
