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

## Direct-comparator evidence matrix: P03/P04/P06 (2026-10-28)

The rows below are an **independent editorial extraction** from the original publisher, university repository or preprint record. Evidence grades mean what was actually inspected, not what type of experiment the authors say they performed. "Physical reported" is **third-party** evidence, never an ARC-RVI measurement. No record is treated as independent confirmation merely because it appears in several RVI study matrices.

| Stable source identifier and study mapping | Inspected material / evidence grade | Source-reported platform and setting | Method and comparator | Reported outcome and uncertainty | Claim boundary / remaining gate |
| --- | --- | --- | --- | --- | --- |
| [10.1109/IROS58592.2024.10802791](https://publications.ait.ac.at/en/publications/visual-quality-inspection-planning-a-model-based-framework-for-ge/) — P03, P06 overlap | **Publisher-affiliated repository abstract and citation only**; full IROS paper not inspected | Simulations **and experiments reported**; exact robot and independent sample count not established by the abstract | Integrates object geometry, imaging visibility and robot kinematics; compared to box-constrained and workspace-sampled pose selection | Abstract asserts improved coverage and fewer poses; **no verified numeric estimate or CI** | Kinematics-aware inspection viewpoint generation was already published; cannot claim its invention. Do not turn an abstract into quantified evidence |
| [10.34726/hss.2026.138640](https://repositum.tuwien.at/handle/20.500.12708/226537) — P03/P04/P06 | **TU Wien thesis repository abstract** (135-page doctoral thesis, not separately peer-reviewed journal evidence); complete thesis methods not appraised | Author reports synthetic and real evaluations of 3-, 6- and 8-DoF systems; not Unitree G1 EDU | Joint camera pose generation, spatial-resolution and photometric visibility, kinematic pose repair, collision/workspace-aware set-coverage route optimisation; exact method baselines require full thesis | Claims fewer poses, improved coverage and shorter time; **sample units, numeric effects and uncertainty not extracted** | Combined photometric quality + feasible viewpoint/path optimisation is **established prior art**. Audit overlap with the 2024 IROS study; do not count thesis and component publications as independent experiments without identifying disjoint datasets |
| [arXiv:2603.16471](https://arxiv.org/abs/2603.16471) — P03/P04 | **Author preprint abstract only**; no numeric paper-level extraction | **Physical mobile-manipulator** pipe-network mock-up experiment reported in a confined environment, not a bipedal robot | Online geometry estimation, information-gain / coverage NBV and stochastic collision-avoidance constraints via vector-field inequalities | Abstract reports reconstruction and full coverage of a simplified pipe network; **no audited denominator, reference surface or CI** | P04 must not claim first physical autonomous NBV inspection. Verify full paper and its evaluator geometry before defining a matching benchmark |
| [10.3390/app16189389](https://www.mdpi.com/2076-3417/16/18/9389) — P06, P03 | **Publisher full HTML: sections 2–3, Tables 1–5, conclusions**; experimental methods and results inspected, not replicated | Single **4-DoF Dobot Magician** eye-in-hand stereo system; 6 scenes × 10 samples = **60 samples**, 4 candidate views per sample | ROI stereo-risk / reliable-coverage gating; constraint-filtered online top-1 viewpoint; compares initial, online proxy and independent operator-selected offline viewpoint; additional heuristic ablations | **Evaluable rate:** initial 70.0%, online proxy 76.7%, manual offline 93.3%. For paired Q differences, the author's 95% bootstrap interval for online minus initial is **[−0.008, 0.060]**, including zero. 30/60 online cases recovered or improved; 30 not | Quality-gated re-observation is prior art. Paper states **no independent reference depth**, so ROI reliability is not validated metric depth accuracy; only six scenes may provide fewer independent units than 60 sample frames. P06 must use independent inspection-valid surface coverage, grouped uncertainty, matched deadline and explicit failure denominator |

**Non-independence flags.** The Staderini 2024 IROS work and Staderini 2026 doctoral thesis are related research outputs with an unknown amount of shared experiment content. Treat them as **two source records but not two independently replicated findings** until datasets, experimental setups and results have been compared. P03/P04/P06 reference the same Bettles and/or Staderini studies as context; shared works are not multiplied into separate support for each hypothesis. Zhao's 60 samples nested within six scenes must not be interpreted as 60 independent physical environments.

**Prospective contrasts after this audit:** P03 compares articulated humanoid safety/whole-body feasibility and accepted surface coverage with matched deadline, not merely kinematic visibility; P04 tests partial unknown geometry against a withheld independent coverage evaluator, not first-use NBV; P06 compares bounded active reacquisition against no-retry, same-view retry, exposure/gain control and finite feasible-view baselines, scoring *independent* inspection validity. The reported 2026 Zhao interval does **not** support a definitive paired mean-Q improvement over initial on that source's own data.

## Humanoid-in-difficult-terrain integration matrix (2026-10-28)

The robot is **bipedal** and the intended site is **complex terrain**,
not a level-floor holonomic inspection platform. Published locomotion
demonstrations on **Unitree G1** and inspection trials in controlled
indoor environments do **not** verify the installed **Unitree G1 EDU**
configuration. The [source-graded direct prior art and primary
source URLs](../../docs/prior-art-critical.md) include RoboInspect,
FAWBC, terrain-consistent reference-guided navigation, WM-LOCO and
perceptive whole-body motion tracking; they prohibit broad "first
humanoid inspection" or "first difficult-terrain G1 locomotion" claims.

| Study | Terrain-conditioned falsifiable addition (prospective) | Independent / unavailable measurement | Existing source risk and required comparison |
| --- | --- | --- | --- |
| **P03** | Does a coupled view/contact-aware route improve inspection-valid area at the same deadline **without allowing out-of-envelope bipedal contact plans**? | Independently checked foot support, slip/collision/torque feasibility and accepted acquired coverage, **not** planned viewpoints | FAWBC and G1 terrain navigation already control rough contacts. Compare geometric only, locomotion-only risk-aware, imaging-only and coupled policies at identical allowed support and sensing |
| **P04** | When next-best-views require unstable or occluded footholds, does uncertainty-aware selection reach a reference-coverage threshold within time? | Hidden target geometry, hidden terrain/support truth, estimated map, verified executed stance | Online NBV/mobile-manipulator work exists; **not** a claim that humanoids invented NBV. Keep missed unreachable regions in denominator and a separate safe-access conditional analysis |
| **P05** | Does terrain-induced torso motion change repeat-camera-pose dispersion for gait-aware vs fixed-delay capture? | Independent exposure-time camera reference, actual stance transition and failed-approach count | G1 locomotion papers report balance or trajectory tracking, not necessarily image registration repeatability; reject time-unsynchronised proxies |
| **P06** | Does terrain/gait-aware quality re-acquisition improve independently accepted inspection images at equal motion budget? | Independent image-quality criterion, exposure-time head motion, all rejected/no-image events | Quality-gated active re-observation exists; independent **inspection-valid** coverage and gait/fall failure accounting must differ from camera quality scores |
| **P07** | Can physical coverage/errors after rough-terrain traversal be predicted from a calibrated contact-and-sensor simulator on held-out sessions? | Independent physical robot/terrain reference, calibrated force/pose/image truth, model validity envelope | G1 simulation-to-hardware results concern **other controllers and hardware**; planar ARC-RVI is outside this domain. No physical data currently exist |
| **P08** | In approved complex terrain, is assessor-blinded autonomous documentation noninferior to manual acquisition for *all assigned required regions*, including safe stops? | Independent human/object/session blocks, actual safe traversability, adjudicated documentation, interventions | RoboInspect already reports supervised indoor physical humanoid inspections. Other G1 studies traverse stairs/rough terrain but do **not** provide the proposed blinded manual-versus-autonomous inspection endpoint |

**Non-overlap of independent evidence:** P03's executed safe view/path
coverage, P04's *online unknown target* budget-capped time, P05's
return-pose dispersion, P06's *image validity* recovery, P07's
physical prediction error and P08's blinded documentation proportion
are distinct primary units/estimands. They may share a site or hardware
calibration **but must report data overlap and not reuse one outcome
as independent support for multiple papers**. Start with virtual,
independently validated contact fixtures; physical G1 EDU terrain motion
remains blocked by [the safety gate](../../docs/safety.md).

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
