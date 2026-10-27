# Experimental methodology

Predefine hypothesis, primary endpoint, effect of interest, sampling unit,
baselines, exclusions, ablations and stopping rule in each `experiments/expXX_*`.

Separate evidence levels:
- Fixture: deterministic synthetic input; validates code behavior only.
- Simulation: generated observations from an explicit geometric, kinematic or physics model.
  Record the model class and limits. The current planar model has no dynamics or image sensor.
- Physics simulation additionally requires controlled dynamics and sensor models.
- Physical experiment: authorized real-world device, safety protocol and
  calibrated measurement system.

Record uncertainty, confidence intervals and failures as well as successes.
Use object- and session-grouped splits, not independent image-level splits for
repeated observations. Replicate across random seeds and environment settings.
An experiment is not complete without a reproducible script and validated data.

## Literature provenance and claim control

The four submitted ARC-RVI literature drafts are **unverified source material**.
The [canonical intake audit](literature.md) records their origin, preliminary
study-specific priorities and the bibliographic validation backlog. Do not
promote the drafts' source counts, reference labels, predicted test statistics,
publication-readiness tiers or claims of a literature gap into experimental
results or manuscripts without independently checking the underlying studies.

Treat object families and acquisition sessions as nested sampling units,
use development-only threshold selection, keep reference labels out of policy
inputs and report wrong-instance risk alongside correct selections and
abstentions. For repeated or crossed conditions, estimate uncertainty at the
independent unit; a fixed number of frames is not a power justification.
