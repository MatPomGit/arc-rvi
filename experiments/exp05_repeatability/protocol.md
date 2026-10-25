# Study 05: Influence of Humanoid Locomotion and Camera Pose on Visual Acquisition Repeatability

**Status:** planned; no results or data collected by this repository.

## Research question
Which motion and pose factors explain variance in repeatable image acquisition?

## Pre-registered hypotheses
- H0: Controlled stabilization does not reduce between-acquisition geometric and focus variation.
- H1: Gait-state-conditioned capture reduces repeatability error at fixed scene and camera settings.

## Baselines
Capture during motion; immediate stop and capture; fixed settling delay.

## Primary endpoint
Within-object variability of camera pose and calibrated focus quality.

## Design and independent unit
Repeated randomized blocks across objects, robot poses, lighting and gait state; mixed-effects analysis with robot session as grouping factor.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper05/manuscript.tex`.
Avoid pseudoreplication of images as independent physical trials; report sensor and pose measurement uncertainty.
