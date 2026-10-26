# Architecture

The shared core contains neutral algorithms and data contracts. A future
orchestrator will connect target localization, navigation, viewpoint selection,
acquisition, quality control and evidence generation via one adapter boundary.

1. Confirm a target identifier.
2. Localize the target and its required visual regions.
3. Determine candidate viewpoints and feasible routes.
4. Execute movement only through a validated safety-controlled robot adapter.
5. Acquire images and evaluate measured quality.
6. Replan/retry if quality or coverage is insufficient.
7. Store a versioned package of images, hashes, provenance and outcomes.

Current implementation: deterministic planar greedy viewpoint baseline, mission
state guards, threshold decisions on supplied measurements, file hashing, paired fixture
benchmarking and a planar geometric simulator. The simulator has a separate observation
contract and never implements physical-device motion. See [the model](simulation.md).
Not implemented: perception, motion control, image feature extraction, real
camera capture, actual physics simulator integration and closed-loop operation.

External analytical models receive a neutral manifest and images; they do not
control motion and are not embedded into this research code.
