# ARC-RVI: critical literature synthesis for P01–P08

**Edition:** 2026-10-28. **Status:** an authorial, *provisional* synthesis of the supplied four long-form Markdown drafts and eight selected bibliographic CSV exports, cross-checked against the repository's already-curated 22 bibliographic metadata records. This is **not** a completed full-text systematic review, not new empirical evidence, and not a novelty certification. Candidate interpretations below must not be converted to factual prevalence estimates.

## Research framing

The coherent scientific question is **how reliably an embodied robot can acquire verifiable inspection observations under coupled geometric, operational, imaging and safety constraints**. It requires separating: (1) finding the requested instance; (2) choosing a visible, physically feasible camera pose; (3) capturing technically acceptable imagery; and (4) producing complete, independently auditable inspection documentation. An image-quality score or navigation success by itself is not an inspection success.

The export inventory contains 1907 mentions and 1695 unverified grouping keys (see [audit](export_audit_2026-10-28.md)). These counts are not a measure of how often a method succeeds, nor evidence that a particular research gap is absent from literature.

## P01 — Reproducible robustness benchmarking

The candidate contribution is an **inspection-specific benchmark** with matched nominal/perturbed scenes, clear object-family separation, predeclared task failures and calibrated inspection-valid outcomes. [VPR-Bench](https://doi.org/10.1007/s11263-021-01469-5) establishes prior practice in controlled viewpoint/appearance evaluation, but does not validate physical humanoid inspection. [ROEP](https://doi.org/10.3390/s26154757) supplies deployment-facing robotics evaluation concepts outside the exact inspection task. A new benchmark must demonstrate construct validity and reproducibility rather than claim a first-ever robotics benchmark.

## P02 — Target identification and localization

Object-level mapping and geometry-aware identification already exist: [Fusion++](https://doi.org/10.1109/3DV.2018.00015) and [RoboEye, preprint](https://doi.org/10.48550/arxiv.2509.14966). ARC-RVI's distinct potential endpoint is **wrong-instance selection**, including target-absent requests and calibrated abstention in clutter. A controlled evaluation needs independent object identities, session-separated visual data, physical reference geometry and methods stronger than synthetic pixel matching. Existing generated 8×8 imagery is fixture evidence, not natural-image recognition.

## P03 — Viewpoint and motion planning

Inspection pose generation constrained by robot kinematics is established in [Staderini et al.](https://doi.org/10.1109/IROS58592.2024.10802791); constrained sensing also appears in [Gemerek et al.](https://doi.org/10.1109/TRO.2022.3180628). [Bettles et al., preprint](https://doi.org/10.48550/arxiv.2603.16471) reports physical mobile-manipulator inspection in clutter. The residual ARC-RVI question is whether a **Unitree G1 EDU-specific, whole-body-feasible** view/motion policy improves accepted coverage under an identical motion-time budget. Exact URDF, sensor frames, stability envelope and collision model are not yet verified on the selected hardware. No claim of first physical NBV inspection is defensible.

## P04 — Active visual coverage

The source export emphasizes next-best-view, geometry uncertainty and coverage optimization. [Surface Edge Explorer](https://doi.org/10.1109/ICRA.2018.8461098) and [Bettles et al.](https://doi.org/10.48550/arxiv.2603.16471) constrain the novelty claim. ARC-RVI should evaluate unknown-object/unknown-surface coverage with **policy-hidden evaluator geometry**, independent surface-area ground truth and bounded acquisition time. Prevent contamination by not using P03's known-mesh oracle metrics as an independent confirmation of P04.

## P05 — Repeatable acquisition geometry

The source material identifies camera extrinsics, relocalization and teach-and-repeat as relevant techniques, but **does not establish a validated evidence base for a quantified humanoid inspection repeatability gap**. The relevant outcomes are repeated camera-to-target translation/rotation errors, target framing and image registration under return visits, with calibrated references and uncertainty. Avoid equating robot-base relocalization error with end-effector camera repeatability. Any specific camera/sensor specification remains conditional on verified G1 EDU configuration.

## P06 — Acquisition quality and recovery

Image control and repeat observation have material prior art: [Shin et al.](https://doi.org/10.1109/IROS40897.2019.8968590), [Kim et al.](https://doi.org/10.1109/TRO.2020.2985597), [Bégin and Hunter](https://doi.org/10.3390/s22030835) and [Zhao et al.](https://doi.org/10.3390/app16189389). A narrow testable contribution is **bounded, quality-triggered reacquisition** with an independent inspection-valid acceptance criterion, compared to exposure optimization and fixed retry rules under equal budget. Do not use optimized sharpness or gradient entropy alone as proof of successful inspection.

## P07 — Simulation-to-real transfer

Domain randomization, calibration, photorealistic simulation and visibility/occlusion modelling are candidate mechanisms represented in the exported search corpus. Yet the provided data do not establish a particular G1 EDU sensor model or a measured sim-to-real generalization error. The primary methodological question is whether **calibrated synthetic visibility and image-quality predictions transfer to independent physical scenes**. Report absolute prediction error, calibration and ranking preservation, stratified by geometry and lighting; avoid assuming that a Gazebo result is a physical effect. A full-text comparator audit for this direction remains pending.

## P08 — End-to-end autonomous documentation

Human-versus-system inspection comparisons already exist in [Aust and Pons](https://doi.org/10.3390/app12042250) and [Kim et al.](https://doi.org/10.3390/drones6110355); [ANYmal field inspection](https://doi.org/10.1007/978-981-15-9460-1_18) and [RoboInspect physical humanoid cases](https://doi.org/10.1016/j.cacaie.2026.100007) constrain novelty further. ARC-RVI can pursue a **blinded, paired comparison of autonomous and manual documentation** with a predeclared noninferiority margin and assessor-independent scores. Assessor agreement, missing targets, operator intervention and failed missions must count as outcomes. A showcase of an autonomous humanoid is not by itself novel.

## Cross-cutting constraints and publication discipline

1. The research platform is the **selected reference Unitree G1 EDU**, not a confirmed integrated robot adapter. Before motion, satisfy authorization, interlocks, safety review, exact sensor/URDF checks and calibrated reference measures.
2. Separate **bibliographic presence**, **abstract-reported results**, **full-text verified methodology**, **reproduced computation**, **simulation observations** and **new physical measurements** in every manuscript.
3. Disclose common datasets, subjects, environments and baselines across papers P01–P08. An eight-part work programme does not automatically yield eight independent publishable findings.
4. Freeze hypotheses, units of independence, splits, baselines, margins and missingness plans before opening any confirmatory held-out data.
5. The identified research gaps are **candidate contrasts**, not demonstrated absence of competing studies. A current systematic search, full-text appraisal and independently verified source-to-claim links remain necessary.

The attached [evidence-to-experiment map](evidence_to_experiments_2026-10-28.md) translates these distinctions into prospective tests. The existing [prior-art appraisal](../../docs/prior-art-critical.md) remains authoritative for its separately checked source-level summaries.
