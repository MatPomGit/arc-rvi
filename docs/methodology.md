# Experimental methodology

Predefine hypothesis, primary endpoint, effect of interest, sampling unit,
baselines, exclusions, ablations and stopping rule in each `experiments/expXX_*`.

Separate evidence levels:
- Fixture: deterministic synthetic input; validates code behavior only.
- Physics simulation: controlled dynamic/sensor model with explicit limitations.
- Physical experiment: authorized real-world device, safety protocol and
  calibrated measurement system.

Record uncertainty, confidence intervals and failures as well as successes.
Use object- and session-grouped splits, not independent image-level splits for
repeated observations. Replicate across random seeds and environment settings.
An experiment is not complete without a reproducible script and validated data.
