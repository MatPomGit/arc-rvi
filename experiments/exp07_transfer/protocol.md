# Study 07: Closing the Sim-to-Real Gap in Autonomous Humanoid Visual Inspection

**Status:** planned; no results or data collected by this repository.

## Research question
Which calibrated stochastic simulator factors predict real inspection performance?

## Pre-registered hypotheses
- H0: Sensor/actuation calibration and targeted randomization do not improve physical transfer.
- H1: Identifiable physical parameters with bounded randomization reduce real-world performance loss.

## Baselines
Nominal simulation only; naive wide domain randomization; calibrated parameters without randomization.

## Primary endpoint
Real-vs-sim error in localization, coverage and run success on matched scenarios.

## Design and independent unit
Use separate calibration and held-out physical sessions; ablate actuator, localization and camera error models.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper07/manuscript.tex`.
Requires sufficient robot access, safety sign-off and independently held-out physical trials.
