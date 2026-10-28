# Commanded vehicle and component photography: mission contract

**Version:** 1.0.0, 2026-10-28. **State:** prospective use case and
software-fixture evidence contract. There is no deployed G1 EDU command,
speech, camera, locomotion or human-return implementation in this change.
Every result from the included examples is `software_fixture_only`.

## Operational scenario and success condition

A human tells the humanoid: **"Photograph that car and return to me"**,
or **"Find the rear bumper of that car, photograph it, and come back."**
The robot must interpret the instruction, identify the *correct physical
instance*, locate the target part when required, execute an approved
photo plan, reject poor-quality views and resume acquisition, then return
to a safe handoff position and verify contact with the requesting human.

`mission_complete = identity_grounded AND part_grounded_if_requested
AND all_approved_slots_independently_accepted AND safe_return_and_handoff`.

This conjunctive rule is intentionally stronger than "robot reached car",
"camera captured N files", "estimated geometric visibility >= threshold",
or "robot returned to its starting coordinates".

## Proposed end-to-end state machine

| Phase | Inputs / required observation | Exit and fail-closed behavior |
| --- | --- | --- |
| 1. Accept task | Voice/text transcript with traceable operator instruction, vehicle descriptor, **vehicle or component** scope, particular front/rear component if needed | Ambiguous terms such as "this car", "the bumper" or "on the left" require a grounded referent and reference frame; request clarification before committing to a target |
| 2. Search and ground instance (P02) | Candidate cars with time-stamped visual/spatial observations, person pointing or scene context if available, posterior uncertainty/abstention | No matching car: report not found; several plausible cars: disambiguate with the human, never silently choose highest score; do not photograph by guessing |
| 3. Ground part (P02) | Mask, 3D localization and parent car instance; explicit `front_bumper` vs `rear_bumper`, vehicle-centered coordinate frame | If exact part or car association cannot be established: do not reclassify another part as success |
| 4. Freeze photo plan | Operator-approved or versioned task template, required regions, shot IDs/view semantics, permitted pose/time budgets | Whole-vehicle shots and one-component shots are different contracts; do not infer that an arbitrary fixed count of photos ensures complete surface inspection |
| 5. Plan and acquire (P03/P04/P05) | Visibility, walking contact/reachability, occlusion, sensor FoV, safe motion, lighting/reflection forecasts, collision-free return reserve | Select safe viewpoints, acquire sequentially; if a region is inaccessible, record **unmet requirement**, do not delete it from the denominator |
| 6. Quality gate / recovery (P06) | Independent ROI mask and target validity, clipping/glare fraction, focus, motion blur, exposure, framing, occlusion, pose uncertainty | Reject photos exceeding *predeclared* limits; first reorient camera/stance where feasible, then calibrated exposure/lighting or polarization if hardware permits; retry within bounded budgets |
| 7. Audit completeness (P04/P08) | Identity-bound photo hashes, distinct required shot IDs, independently accepted view/region assessments and missing-slot ledger | Every assigned slot must be satisfied by genuine quality-accepted evidence; duplicates and wrong-car images never count; report partial coverage honestly |
| 8. Return and handoff (P08) | Operator staging anchor, safe return route, current person rendezvous information and operator acknowledgement | A verified anchor alone is not a person handoff; if operator moved or return is unsafe, stop at an authorised safe holding location and request assistance, **not an open-ended human pursuit** |

The physical controller may **never** read an author-generated JSON verdict
as permission to walk, touch a vehicle or approach a person. Permission,
dynamic stability, contact/traction constraints, human separation, fall
zone, local hazard stopping and emergency takeover are independent,
hardware-verified safety gates. A parked car and a person's proximity
create separate collision/damage risks.

## Instruction resolution and target binding

The request must retain the original human utterance and an auditable
structured description (attributes, relations and directional reference
frame). Model-generated text is not proof of identity. Candidate association
requires observations with source/time and uncertainty; the system must
support **target absent**, **two matching cars**, **wrong instance**, and
**vehicle present but bumper not visible**. For multiple matching candidates,
an explicit human clarification is necessary before committing to a single
instance. Persist `vehicle_instance_id` across view changes and couple
`part_label` to the **same parent instance**.

A named semantic part does not prove that a precise photograph can be
taken. The part mask, body orientation and camera-to-target transform
must be estimated, checked and accompanied by uncertainty. In particular,
front/rear are defined in a **vehicle-centered reference frame**, not
relative to the direction the robot is facing.

## Coverage contract

Two task families:

- **Whole vehicle:** an *explicit* complete-view/required-region
  checklist authorised before flight/walking. An eight-direction
  example (front, front-left, left, rear-left, rear, rear-right, right,
  front-right) is bundled as a **synthetic example only**; it does not
  establish real roof, wheel, underbody, glass or masked-surface coverage.
  Required regions must be specified by the user/protocol and independently
  measured for the actual desired inspection.
- **Single part:** required part label and parent car, for example
  `rear_bumper` plus approved head-on and oblique shots. Do not require
  photographing the entire car for a bumper-only instruction.

The software contract uses `accepted_slots / assigned_slots`, where
`assigned_slots` is fixed **before** capture, including hard or inaccessible
views. P04 geometric coverage is *a separate estimand* requiring withheld
surface truth; P08 valid-region completion is not interchangeable with
P03 viewpoint reachability or P06 image-quality classification.

For reproducible **observed-pixel** ROI clipping/brightness checks on locally annotated photographs, see [the image-quality audit](vehicle-image-qa.md). This is a separate, read-only image analysis stage: its photometric pass **cannot** by itself satisfy independent photo validity or verify car identity.

## Strongly reflective paint: active photometric viewpoint planning

Metallic paint, varnish, glazing and chrome introduce directional
reflections and highlights. Candidate poses must be evaluated under
at least geometry/occlusion + safe kinematics + photometric visibility.
A useful *proposed* objective (not a validated scoring model) is:

`utility(v) = expected new valid required-region coverage(v)
- lambda_g * specular/clipping risk(v)
- lambda_t * mission travel and capture time(v)
- lambda_s * safety risk(v)`, with hard infeasibility rejection first.

The photometric risk should be estimated in a **vehicle/part ROI**,
including saturated highlight masks, local contrast loss, pose and
illumination variability. Whole-image exposure averages are insufficient:
a well-exposed background can coexist with an unusable bumper region.
Any BRDF-based rendering (e.g., Cook–Torrance) requires calibrated
material/light assumptions; only on-image diagnostics are observable
until the lighting and sensor model are validated.

For a failed part-region photo, the following *experimental* recovery
sequence must be compared, not simply assumed optimal: move to a
different safe incidence angle and take another view; adjust sensor
exposure/gain; optionally use polarization/HDR/illumination change **only
after the actual hardware's optical transfer, synchronization and
exposure penalty are independently calibrated**. Do not assert that a
polarizer completely removes reflections, or that lower glare fraction
automatically proves defect visibility.

Record **failed images, re-aim attempts, motion time, aborted safe
repositions and total mission deadline**. Re-taking the same incorrect
view repeatedly without a budget is not an acceptable strategy.

## Exploratory glare-aware viewpoint selector (fixture-only)

A deterministic [predicted-view selector](https://github.com/MatPomGit/arc-rvi/blob/main/src/rvi/photometric_view.py)
now implements a **toy ranking baseline** for the prospective P03/P06
comparison, independent of robot hardware and image acquisition.
It consumes *supplied predictions* for each candidate camera pose:
ROI-valid fraction, specular-glare fraction, visibility proxy, contact
and collision **proxies**, outbound/capture/return time plus an extra
return buffer. It first rejects predicted-infeasible poses and only then
ranks feasible candidates:

`score = predicted_valid_roi - lambda_glare * predicted_glare_fraction
         - lambda_time * (outbound + capture + return + buffer) / remaining_time`.

Every weight and limit is explicit in the input. Ties are resolved
deterministically by candidate ID. If no candidate meets the limits or
the return reserve, the selector **abstains** instead of recommending an
unsafe or high-glare shot. Its score never substitutes for independent
**observed image QC** after a real exposure.

Try the [invented reflective bumper scenario](https://github.com/MatPomGit/arc-rvi/blob/main/simulation/suites/vehicle_glare_viewpoint_fixture.json):
direct view with a large predicted reflection, oblique lower-glare view,
low-glare but unsuitable support pose, and a distant position that
violates the return deadline.

```bash
python scripts/select_vehicle_view.py simulation/suites/vehicle_glare_viewpoint_fixture.json
```

This example selects the synthetic oblique view, **not** a physical
point for Unitree G1 EDU. The static feasibility flags are declared
fixtures, not independent contact, dynamics or obstacle evidence.
Real anti-glare control requires a calibrated paint/light/BRDF or
on-image prediction model, approved hardware pose and return route,
and actual independently assessed photographs. No such calibrated
model or trial is supplied in this PR.

## Operator return, safety and data protection

At the start, establish an operator-designated, bounded handoff anchor.
Return is scored only after (1) supported route and safe arrival,
(2) presence/recontact at the operator handoff, and (3) positive
acknowledgement. The requester's changing position must not trigger
unconstrained autonomous following. If the human is absent, stand by in
a designated safe location, notify and escalate to the operator; do not
mark `returned` as true.

Vehicle number plates and bystanders may occur in imagery: define
a legal/ethical capture context, minimise incidental collection, and
keep raw images and location metadata access-controlled. Images are
not checked into a public research repository by default. Log camera
configuration, timestamps, shot ID, identity/part decisions, immutable
image digest, quality decision and the operator handoff status.

## Offline fixture evaluator

The [mission evaluator source](https://github.com/MatPomGit/arc-rvi/blob/main/src/rvi/vehicle_mission.py)
is intentionally separated from the locomotion/ROS 2 SDK adapter.
These two canonical, **invented** traces are for software checks only:
[whole-car fixture](https://github.com/MatPomGit/arc-rvi/blob/main/simulation/suites/vehicle_photo_mission_whole_car_fixture.json)
and [rear-bumper fixture](https://github.com/MatPomGit/arc-rvi/blob/main/simulation/suites/vehicle_photo_mission_bumper_fixture.json).

From a checkout:

```bash
python scripts/assess_vehicle_mission.py simulation/suites/vehicle_photo_mission_whole_car_fixture.json
python scripts/assess_vehicle_mission.py simulation/suites/vehicle_photo_mission_bumper_fixture.json
python scripts/validate.py
```

The bumper fixture contains a deliberate glare rejection followed by an
independently acceptable reshoot. The full-car fixture has two plausible
vehicles, **human clarification** and eight independent example slots.
Its `fixture_complete` output is **not an empirical rate**, a
demonstration of actual ASR/vision/robot movement, an assessment of true
surface completeness or verification of a live person handoff.

## Study-specific falsifiable additions, without duplicating results

| Paper | Prospective car-mission hypothesis / endpoint | Important comparator or confound |
| --- | --- | --- |
| [P02](../experiments/exp02_localization/protocol.md) | Wrong car/part binding with abstention, multi-car ambiguity and no-target requests; identity-error risk per independent object-set/session | Appearance-only, spatial-only, fused + human clarification; active language grounding exists |
| [P03](../experiments/exp03_viewpoint_planning/protocol.md) | G1 EDU feasible camera stances for car/bumper regions including constrained parking terrain; accepted area under matched time | Kinematics-and-photometric planner vs decoupled baseline, identical candidate stances |
| [P04](../experiments/exp04_active_coverage/protocol.md) | Required yet unobserved body regions covered under partial geometry with withheld reference | Frontier/NBV, reflective-surface-aware NBV, same access and mission budget |
| [P05](../experiments/exp05_repeatability/protocol.md) | Return visits to the **same part** and camera-to-part pose error under bipedal gait/settling | Fixed-delay vs pose-settled capture; calibrated independent reference |
| [P06](../experiments/exp06_quality_control/protocol.md) | Accepted valid ROI fraction after glare-triggered bounded reacquisition | Same-view retry, exposure-only, incidence reorientation, optional polarized/acquisition-aware arm |
| [P07](../experiments/exp07_transfer/protocol.md) | Prediction calibration of glare/visibility and safe reachable views from simulation to physical vehicles | Independent held-out materials, lighting, scenes, hardware calibration |
| [P08](../experiments/exp08_field_validation/protocol.md) | Entire commanded mission: correct referent + accepted required views + verified return/handoff | Standardized manual capture; separate safety, missing views and intervention denominators |

The research hypotheses remain **unfrozen**; task thresholds, independent
scene/session partitions, specimen rights, reference calibrations, matched
baseline implementations and practical safety approvals are missing.

## Relevant prior art (graded as abstract/primary metadata, not replicated)

- [LEGS-POMDP, He et al., HRI 2026](https://arxiv.org/abs/2603.04705):
  joint uncertain language/gesture target *identity and location* in
  active search; robot demonstration reported, not tested on G1 EDU cars.
  Ambiguous instruction resolution cannot be claimed categorically novel.
- [LINGO-Space, Kim et al., AAAI 2024](https://doi.org/10.1609/aaai.v38i9.28898):
  probabilistic spatial grounding and incremental referent disambiguation.
- [Staderini et al., 3DV 2024](https://doi.org/10.1109/3DV62453.2024.00108):
  photometric visibility matrix using BRDF for reflective inspection
  viewpoints (conference abstract/repository metadata inspected).
  The contribution is **not first-ever reflection-aware view planning**.
- [van Ruitenbeek & Bhulai, *Machine Vision and Applications* 2022](https://doi.org/10.1007/s00138-022-01295-w):
  vehicle damage inspection with multi-view robustness to reflection
  (publisher abstract inspected); not a walking humanoid acquisition controller.
- [He et al., *Journal of Manufacturing Systems* 2024](https://doi.org/10.1016/j.jmsy.2023.11.014):
  explicitly addresses specular car-body defect imagery
  (publisher preview); don't extrapolate a field robot effect.
- [Zhang et al., *Optics and Lasers in Engineering* 2024](https://doi.org/10.1016/j.optlaseng.2024.108418):
  highly reflective part viewpoint-measurability includes angular and
  exposure criteria, not a physical G1 EDU mission.
- [FRA-NBV, Preziosa et al. 2026](https://doi.org/10.1109/LRA.2026.3728374):
  reflectivity-aware missing-depth reacquisition; direct comparator to P04/P06.
- [Dong et al., AAAI 2024](https://doi.org/10.1609/aaai.v38i2.27922):
  polarization material cues for car detection; **not** proof that an
  uncalibrated G1 EDU camera has polarization sensing.

**Novelty boundary:** combining speech grounding, car instance identification,
part localization, reflective-surface acquisition, completeness audit and
safe human return is an integrative **hypothesis**, not yet demonstrated
as an unprecedented scientific algorithm or executed physical system.
