# Full-dive VR systems architecture

This is a requirements diagram, not a claim that the integrated system exists. Solid arrows describe ordinary information flows. Dashed arrows identify unresolved management of physical movement and conflicting physical sensory input.

```mermaid
flowchart TB
    U["Conscious user: intentions, perception, learning"]
    R["Readout: EMG, peripheral nerves, EEG, ECoG, intracortical"]
    D["Intent decoder: action, idle state, uncertainty"]
    W["Virtual world and body: physics, contacts, avatar dynamics"]
    E["Sensory encoders: models for each sensory system"]
    V["Vision: optical display or neural prosthesis"]
    A["Hearing: headphones or auditory interface"]
    H["Body feedback: touch, force, temperature"]
    P["Position and balance: proprioceptive and vestibular interfaces"]
    B["Physical body and environment: natural sensation and movement"]
    M["Movement separation: voluntary stillness now; active suppression unresolved"]
    G["Management of conflicting physical sensory input: unresolved"]
    C["Calibration and adaptation: performance, drift, percept reports"]
    S["Independent safety controller: limits, watchdog, exit, recovery"]

    U --> R --> D --> W --> E
    E --> V --> U
    E --> A --> U
    E --> H --> U
    E --> P --> U
    U --> B
    B --> U
    B --> R
    D -.-> M
    M -.-> B
    B -.-> G
    G -.-> U
    R --> C
    U --> C
    C --> D
    C --> E
    S --> D
    S --> E
    S --> M
    S --> G
```

## Readout and feedback form different paths

Readout estimates voluntary action. Feedback generates sensations that help the user control that action. A working decoder does not establish a working sensory encoder.

The physical body continues to supply sensory input. Writing a virtual limb-position signal does not necessarily remove the real limb-position signal. Preventing physical displacement does not remove muscle activation, effort, or afferent feedback.

## Start with the accessible path

The first project uses surface EMG, a virtual hand, and mechanical vibration. Ordinary vision and hearing remain available. The hand is supported and physical movement is measured. The project calls vibration-based force cues sensory substitution rather than natural touch restoration.

See the [feasibility study](feasibility-study.md) for evidence and the [first-project spec](../specs/001-stationary-virtual-hand.md) for proposed implementation requirements.
