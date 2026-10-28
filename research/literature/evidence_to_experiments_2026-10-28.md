# ARC-RVI evidence-to-experiment and publication gate map

**Status 2026-10-28:** prospective study design synthesized from supplied literature exports, not a report of performed trials. Endpoints and margins are candidates to be finalized in the canonical [study-specific protocols](../../experiments/README.md); do not override an already frozen protocol.

| Study | Prospective contrast / falsifiable question | Primary endpoint to predefine | Required comparator | Blocking evidence |
| --- | --- | --- | --- | --- |
| P01 | Does perturbation-aware evaluation change reproducibility/robustness ranking versus nominal-only testing? | Family-paired difference in inspection-valid task success | Identical methods, matched nominal vs perturbation | Independent scene-family sampling, calibrated target validity |
| P02 | Does geometry+appearance+abstention reduce wrong-instance selections? | Wrong-instance rate per eligible request, with abstention cost | Geometry-only, appearance-only, fused, reject option | Real-image session/identity-disjoint data and ground truth |
| P03 | Does coupled bipedal feasibility plus view quality improve accepted coverage under an equal budget? | Required inspection-valid area within time/safety constraints | View-only, motion-only, coupled; same cost and constraints | Verified G1 EDU kinematics, calibration and safe platform |
| P04 | Does observation-driven NBV improve unknown-surface inspected coverage? | Accepted visible surface fraction from withheld evaluator geometry | Frontier, geometric NBV, uncertainty-aware NBV | No planner access to test geometry; independent scene families |
| P05 | Is camera-to-target return pose reproducible within a defined tolerance? | Repeat-visit translation and orientation error, with uncertainty | Teach-repeat, landmark relocalization, visual servo | Calibrated external reference and repeated physical sessions |
| P06 | Does bounded quality-triggered reacquisition increase acceptable evidence versus fixed retries? | Inspection-valid image/area proportion at matched mission time | No-retry, fixed retry, exposure/gain optimisation | Independent quality rater and failure/no-image accounting |
| P07 | Are simulation-based visibility and quality predictions calibrated to hardware? | Prediction-error distribution on held-out physical scenes | Uncalibrated simulation, calibrated simulation, simple empirical baseline | Independent physical reference and sensor calibration |
| P08 | Is autonomous documentation noninferior to manual documentation? | Assessor-blinded completeness/validity difference | Human manual, autonomous, optionally teleoperated | Prespecified margin, independent assessor, safety approval, complete failures |

## Common statistical design

The **independent experimental unit** must be a physical scene, distinct target/object family or visit/session as appropriate, not an individual correlated frame. Plan blocked or hierarchical comparisons to account for repeated views of the same scene and multiple trials per operator. Predefine all stratification factors (clutter, occlusion, illumination, motion, geometry), randomized order, censoring, failed trials, and confidence intervals; avoid frame-level pseudoreplication. For P08, noninferiority requires an independently justified margin, adequate power and a specified intention-to-evaluate population; a non-significant superiority test does not establish noninferiority.

## Source verification checklist

For each paper ultimately cited as a direct comparator, record: DOI/publisher or preprint version, title/authors/year, methods section inspected, robot and sensor, physical/simulated setting, independent units, ground-truth reference, comparator fairness, outcome definition, numerical result and uncertainty, study limitations, and the precise ARC-RVI claim supported. Catalogue metadata reviewed by an editor does not count as full-text appraisal.

## Prior-art exclusions from novelty claims

- **P03–P04:** physical manipulator NBV and kinematics-aware inspection planning exist; restrict claims to a tested, justified humanoid-specific result.
- **P06:** proactive camera tuning and quality-aware re-observation exist; assess independent inspection acceptance, not mere image quality.
- **P08:** humanoid inspection demonstrations and human-versus-technology comparisons exist; assess blinded documentation quality under paired tasks.
- **P05/P07:** insufficient validated study-level extraction in supplied inputs for strong claims; mark as novelty **undetermined**.

## Priority and go/no-go

Initially prioritize **P01/P02 offline validation**, then matched P03/P04/P06 simulation with explicit separation of evaluation truth, and only afterward authorized physical P03/P05/P07/P08 studies. The present status is **NO-GO for claims of empirical superiority, publication-ready effects, or physical G1 EDU validation**. The work programme can support protocol drafting and study feasibility, but final journal selection depends on completed, independently evaluated results.

Sources: [export audit](export_audit_2026-10-28.md), [critical synthesis](critical_synthesis_2026-10-28.md), [prior-art appraisal](../../docs/prior-art-critical.md), [curated DOI records](verified_doi_metadata.json).
