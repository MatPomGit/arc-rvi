# Research program

Version: 1.1.0

Eight prospective studies share infrastructure but answer different questions.
Protocols are design drafts. Numerical thresholds, sample sizes, implemented methods
and confirmation partitions must be frozen before confirmatory collection.

| Study | Primary question and analysis | Distinct evidence requirement |
| --- | --- | --- |
| [01](exp01_benchmark/protocol.md) | Method differences in nominal-to-challenge success loss | Diverse validated simulation scenes |
| [02](exp02_localization/protocol.md) | Wrong-instance selection under distractors | Held-out identities and independent pose reference |
| [03](exp03_viewpoint_planning/protocol.md) | Valid coverage under a common motion budget | Articulated feasibility and collision model |
| [04](exp04_active_coverage/protocol.md) | Budget-capped time to target coverage | Partial observations and hidden reference surfaces |
| [05](exp05_repeatability/protocol.md) | Repeat-acquisition position precision | Independent physical pose measurements |
| [06](exp06_quality_control/protocol.md) | Valid coverage gained through recovery | Independent quality evaluation and attempt logs |
| [07](exp07_transfer/protocol.md) | Error of predicted physical coverage | Disjoint calibration and physical confirmation sessions |
| [08](exp08_field_validation/protocol.md) | Coverage non-inferiority against manual acquisition | Blinded assessment of complete physical workflows |

## Publication boundaries

Study 01 evaluates the benchmark's ability to distinguish conditions and methods.
It does not establish the novelty of the methods used as references.
Study 02 owns identity-assignment analysis. Study 03 owns coupled planning with
known candidate geometry; study 04 owns online selection under incomplete geometry.
Study 05 owns the capture-stability mechanism; study 06 owns recovery decisions.
Study 07 evaluates simulation predictions with a fixed policy. Study 08 evaluates
the integrated workflow against manual acquisition.

Data may be shared when rights permit, but each paper must identify reused objects,
sessions, methods and tables. Keep primary contrasts distinct. Cite related manuscripts
and explain shared evidence. Do not count the same result as two independent validations.
Eight folders are candidate contributions; consolidate papers if evidence does not
support distinct scientific contributions. Novelty requires a verified literature review.

## Implementation order and acceptance

1. Implement study 01's fixture-level trial recorder, paired method runner and scoring.
   Acceptance: hand-calculable successes, partial outcomes and failures reproduce exactly.
2. Add the simulator adapter, reference surfaces and benchmark baselines.
   Acceptance: documented coordinate, visibility, collision and timing checks pass.
3. Pilot studies 02 and 03 on the benchmark; add partial geometry for study 04.
   Acceptance: hold-out partitions are fixed and evaluator data cannot enter the methods.
4. Calibrate physical acquisition for study 05; implement independent quality scoring
   and bounded recovery for study 06. Acceptance: measurements and failures are traceable.
5. Fit study 07 only on calibration sessions; then collect held-out transfer trials.
   Acceptance: predictions are committed before physical confirmation results are opened.
6. Run study 08 after integration and the required physical and participant procedures.
   Acceptance: margin, power plan, assessment and intervention rules are frozen.

Studies 02 through 06 can progress in parallel after their dependencies are met.
Each confirmation study requires the [analysis plan](analysis/README.md),
[provenance contract](../docs/reproducibility.md) and its protocol-specific gates.
