# ARC-RVI research plan

Version: 1.0.0

ARC-RVI is a separate line in the ARC research portfolio. Its canonical status is
[PROJECT_STATE.yaml](PROJECT_STATE.yaml). The [eight-study index](experiments/README.md)
defines distinct scientific questions, publication boundaries and dependencies.
The controller maintains the portfolio index; scientific claims remain in this repository.

## Research sequence

| Package | Deliverable | Acceptance |
| --- | --- | --- |
| RVI-01 | Reproducible scenes and paired policy evaluation | Independent units, split manifest, hashes, preserved failures |
| RVI-02 | Target identity and coupled view/path planning | Independent ground truth, held-out geometry, feasible motion |
| RVI-03 | Adaptive coverage and quality-guided recovery | Estimated coverage separated from reference coverage; bounded retry cost |
| RVI-04 | Physical repeatability and transfer calibration | Independently measured pose/time and separate calibration sessions |
| RVI-05 | End-to-end documentation comparison | Frozen margin, assessment rules and applicable physical/participant procedures |
| RVI-06 | Publication readiness per study | Verified literature, distinct primary analysis and reproducible evidence |

The reference robot for planned simulation-model validation and authorized
physical tests is **Unitree G1 EDU** (`config/robot.yaml`). This selection
does not enable hardware control or assert ownership of a specific variant.
Retain vendor-neutral research algorithms and verify the particular robot,
sensors, SDK, kinematics, coordinate frames and safety model before deployment.

The software currently supports fixtures and planar geometric/kinematic simulation.
Candidate visibility comes from known geometry. Physics, physical acquisition and
unknown-geometry perception require separate implementations and validation.
The smoke suites check software arithmetic; they do not establish method superiority.

## Relationship to other ARC work

[ARC-RGBT](https://github.com/MatPomGit/arc-rgbt) studies multimodal sensing and fusion.
ARC-RVI studies target selection, acquisition geometry, coverage and documentation.
A future sensor exchange must preserve acquisition timestamps, native resolution,
calibration, frame conventions and file hashes. This is a proposed boundary;
no cross-repository runtime integration or shared dataset is implemented.

Reuse data only after checking provenance, rights, group-separated splits and overlap
between primary analyses. Keep each project's hypotheses and publication claims distinct.
Do not copy confidential source material or identities into public research artifacts.

## Execution

Use the existing controller and repository instructions. Registration is not a deployment
receipt or a new execution policy. Do not add another scheduler, task queue or merge path.
Run `python scripts/validate.py` before recording new software verification evidence.
Record exact revisions in PR evidence; physical results need independently traceable measurements.
