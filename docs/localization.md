# Study 02: Instance-level localization

**Status:** exploratory method and fixture-validation design. See the
[prospective study protocol](../experiments/exp02_localization/protocol.md)
for the scientific question, sampling unit, primary analysis and freeze gates.
No trained visual feature extractor, localization sensor, physical device or
independent reference pose is available in this codebase.

## Problem definition

For a target request \(q\), the system observes a set of anonymous candidate
instances \(D_q=\{d_1,\ldots,d_n\}\). It must return **one candidate identity or
abstain**. An absent target is a valid trial, not an input error. The
evaluation-only reference \(y_q\) is either a candidate identity or null.

The decision must not receive \(y_q\), hidden reference geometry, evaluation
split labels or future observations. The evaluator may inspect these fields
only after a frozen prediction is recorded. Selection and pose estimation
are distinct tasks: a geometrically close pose does not excuse choosing the
wrong object.

## Initial deterministic reference methods

The initial fixture-level API accepts **precomputed, normalized distances**
in \([0,1]\). They are not extracted from images by ARC-RVI.

| Method | Lower-is-better score | Meaning |
| --- | --- | --- |
| `visual` | appearance distance | Synthetic appearance reference |
| `spatial` | spatial distance | Synthetic spatial association reference |
| `fused` | average of appearance and spatial distance | Equal-weight illustrative fusion |

Each method ranks the same candidate set independently. A method abstains when
there is no candidate, its best score exceeds the declared threshold, or the
two best scores differ by no more than the declared ambiguity margin. These
thresholds are illustrative fixture parameters, **not** validated operating
settings. Exact ties also abstain rather than silently relying on input order.

The scores intentionally encode the ranking problem but not vision, temporal
association, perspective projection, identity embeddings, occlusion handling,
camera calibration or sensor uncertainty. Better performance on constructed
scores cannot establish the proposed scientific fusion hypothesis.

## Exploratory sensor-based association

The existing `rvi localize` command also accepts a simulated sensor study:

```bash
rvi localize --sensor-study simulation/suites/localization_sensor_demo.json --output results/study02_sensor.json
```

This uses the [planar feature sensor](simulation.md). A target request
supplies an expected horizontal pixel and range cue. Methods compare that cue
with **actually generated anonymous sensor detections** using three fixed
scores: `bearing_proxy` (pixel mismatch/width), `range_proxy`
(range mismatch/maximum scene range), and `joint_proxy` (their mean).
This reuses the existing selector and abstention rules; the labels intentionally
do **not** claim visual appearance recognition or metric 3D pose recovery.

Patch identity and detection correspondence are withheld until selection
is complete. The report keeps `observations[].policy` separate from
`observations[].evaluator`, includes source/input/sensor hashes and records
every matched method/request, including absent targets, missing observations,
wrong selections and abstentions. A one-scene synthetic example is a software
replay, not independent experimental replication. Association remains based
on externally supplied cues; the source, uncertainty and validity of those
cues have not been calibrated.

This is partial progress on [Issue #23](https://github.com/MatPomGit/arc-rvi/issues/23)
and [Issue #24](https://github.com/MatPomGit/arc-rvi/issues/24).
Natural-image descriptors, real session separation, physical pose metrology
and prospective confirmation remain outstanding. Synthetic grayscale matching
is described below.

## Reproduce the software fixture

From the repository root, after `python -m pip install -e .`:

```bash
rvi localize --fixture simulation/suites/localization_fixture.json --output results/localization.json
```

The input is a versioned JSON fixture with `schema_version`,
`evidence_type: fixture`, a suite identifier, `threshold`,
`ambiguity_margin` and a nonempty `requests` array.
Each request has a unique `request_id`, evaluator-only
`ground_truth_id` (nullable) and candidate records with `id`,
`visual_distance` and `spatial_distance`. IDs must be unique within
each request. The parser rejects duplicate JSON keys, NaN, Infinity,
nonfinite or out-of-range scores and unexpected schema fields.

The report records the original fixture-byte SHA-256, package source hashes,
one prediction per method/request, explicit abstention reasons, and risk
denominators including absent-target requests. The output file is never
overwritten. The three-request hand-check demonstrates arithmetic and
error handling only; it is not a sample for inference.

## Research outcomes

For every eligible request, define wrong-instance selection as

\[
W_q = {\bf 1}[\widehat y_q \ne \varnothing
             \land \widehat y_q \ne y_q].
\]

Here \(\widehat y_q\) is the selected identity or abstention and \(y_q\)
is the reference identity or null. In an absent-target request, **any
selection is wrong**; abstaining is a correct rejection. In a present-target
request, abstention is not a wrong selection but must count in the
denominator and in the separate abstention rate.

The primary risk is \(\sum_q W_q/N\), where \(N\) includes **all eligible
requests**, not only confident predictions. Publish correct-selection rate,
correct-rejection rate on absent-target trials, abstention rate, and all
method-specific denominators. Do not reinterpret a zero wrong-selection
rate from an always-abstaining algorithm as evidence of localization ability.

The protocol's independent unit is an **object-set/session block**. Requests
and repeated frames are nested within that unit. For later paired inference,
first aggregate within each independent block and resample blocks, not frames.
Split by object identity and acquisition session. Report present-target and
absent-target strata separately. No confidence intervals are warranted from
the included hand-constructed fixtures.

## Proposed progression and acceptance gates

1. **Fixture arithmetic.** Verify score ordering, ties, threshold equality,
   null targets, duplicate IDs, nonfinite values and preserved abstentions.
   Hash exact inputs and archive the source revision.
2. **Observation adapter.** Define frame IDs, UTC timestamps, camera-to-world
   transforms, coordinate conventions, calibration hashes, confidence ranges
   and a no-reference-leakage boundary. Anonymous 1D features and separate
   evaluation records are implemented; full imaging and calibration are pending.
3. **Simulation study.** Create independent object-set families with
   distractor similarity, separation and occlusion crossed prospectively;
   freeze the input representations and record simulator/renderer limitations.
   The existing planar coverage simulator has **no image renderer**.
4. **Pose and identity validation.** Verify projected reference pose
   independently, including calibration uncertainty. Pose-error statistics
   are conditional on correct identity assignments; wrong IDs and absent
   pose measurements require explicit failure handling.
5. **Confirmation.** Lock comparison, reference method, thresholds, minimum
   correct-selection rate, family/session splits, sample-size calculation and
   analysis code before inspecting a new held-out sample.

A frozen protocol release is not equivalent to public preregistration.
Any move from simulation to authorized physical measurements must follow the
[physical safety](safety.md) and
[reproducibility](reproducibility.md) requirements.

## Interpretation

This work is a *reference implementation and experimental design*, not a
validated identity recognizer or a closed-loop robotics component. The
fixture evaluator cannot be used to control an inspection robot. Identity
assignment remains the distinct primary contribution proposed for Study 02;
planning and coverage belong to Studies 03–04.


## Group-separated factorial pilot (P02)

The exploratory generator extends the one-scene proxy replay with **separate
synthetic object-set families**, two distractor separations (near/far), two
target-visibility conditions (clear/blocked) and matched **present / absent
identity** requests. Replicated sensor captures remain *nested within family*.

```bash
rvi localize-population --spec simulation/conditions/study02_population_pilot.json --output-dir results/study02_population
rvi localize --population-manifest results/study02_population/manifest.json --partition pilot --output results/study02_pilot.json
```

The public specification uses two development families, three pilot families,
two holdout families, and two captures per cell. Generated scenes, per-scene
sensor-study inputs and manifest records carry SHA-256 digests. A model-family
layout is drawn once and reused across factorial conditions. The study reports
a paired method comparison with **equal weight per family**, explicit
wrong-selection/abstention counts and present/absent factor strata. Positive
`paired_difference_joint_minus_bearing` indicates worse joint-proxy risk.
This is descriptive; there are **no confidence intervals or significance tests**.

Only `development` and `pilot` are accepted by this analysis command. It
does **not** read holdout scene/study contents. The generated holdout is public,
so it is not blinded or independently preregistered. Every absent-target
request uses a plausible hard-negative cue near a distractor, and all selected
detections are matched to evaluator-only identity *after* decision. Physical
absence, scene realism and measured sensor calibration are not established.

**Remaining gaps:** images/appearance features, truly near-identical visual
objects, temporal re-identification, independent session draws, grounded pose
uncertainty and the frozen confirmatory comparison. The controlled "separation"
is planar angular/geometric separation, **not visual similarity**.


## Generated grayscale image-patch experiment (v1.18)

The next exploratory Study 02 increment adds **synthetic 8×8 grayscale
patches**, not RGB frames from a camera. Identity-specific binary-intensity
templates are generated once for each object-set family. The distractor
differs from the target in exactly 4 pixels (similar) or 40 pixels
(distinct); the per-frame renderer applies reproducible ±5 gray-level
pixel noise and a shared ±6 gray-level simulated-session luminance offset.

Each detection receives only an anonymous `gray8_8x8` array. The policy
matches a target-request image template using normalized mean absolute
pixel error (MAE), a separate range mismatch, or their equal-weight mean.
The privileged generator uses geometry-to-instance correspondence to render
the synthetic crops, **but correspondence is not an input to the selector**.
An absent request uses a template from a third object that is not in the
scene. Template ownership, camera projection, identity reference and
final scoring are simulation constructs, not independent physical truth.

```bash
rvi localize-population --spec simulation/conditions/study02_image_pilot.json --output-dir results/study02_images
rvi localize --population-manifest results/study02_images/manifest.json --partition pilot --output results/study02_image_pilot.json
```

The public configuration crosses 2 planar separations × 2 target visibility
states × 2 synthetic appearance levels, with 2 correlated captures per cell.
Family groups are disjoint between development, pilot and holdout; a
`session_id` groups repeated observations within each family and is **not**
equivalent to an independently collected session. Every image-study input
and generated scene is covered by the SHA-256 manifest. Holdout evaluation
remains prohibited by the exploratory CLI, and the public holdout is not blind.

Reports preserve missing detections, wrong instances, correct selections,
correct rejections and abstentions. The unit for descriptive contrasts is the
**synthetic family**, not the individual pixel, frame or request. An
`appearance_range − appearance` wrong-selection risk difference below zero
favours fusion on this artificial sample only. No confidence intervals,
significance tests, real-image generalization or physical claims are produced.

This adds actual numeric **pixel-array matching**, but does *not* implement
recognition from natural images, trained embeddings, 3D pose estimation,
physical timestamps, synchronized sensors or independently calibrated
ground truth. Further work must replace synthetic crops with
rights-cleared measured imagery and frozen object/session-disjoint
validation before the proposed scientific hypothesis can be assessed.


## Offline image-crop input from local datasets (v1.19)

The next step accepts **operator-supplied grayscale image crops** as real
file bytes, rather than generating pixels from a known scene. The reader
supports Portable Graymap **P2/P5, 8-bit, maxval 255**, cropped images
with equal dimensions (up to 256×256). Convert any rights-cleared PNG/JPEG
crops to PGM *outside* this package before importing; the tool does not
segment objects, register cameras, resample images, or infer depth.

```bash
rvi localize --image-manifest /local/private_study02/manifest.json \
  --partition pilot --output results/study02_local_images.json
```

The dataset is read-only. Its manifest declares: `schema_version=1.0.0`,
`study_id=02`, `evidence_type=image_observation`,
`stage=exploratory_not_confirmatory`,
`data_origin=synthetic_test|operator_supplied`,
`data_rights=operator_declared_authorized`, `threshold`,
`ambiguity_margin`, `max_range_m`, and `records`. Each record has
a disjoint `object_family_id`, a unique `session_id`, a partition
(`development`, `pilot`, or `holdout`) and two SHA-256-pinned
file references (`observations` and `reference`), in the form
`{"path": "sessions/s01.json", "sha256": "<64 lowercase hex digits>"}`.

Each observation file uses `schema_version=1.0.0`, `session_id` and
`requests`. A request has `request_id`, timezone-aware
`timestamp_utc`, `status=captured|missing_frame`,
`expected_range_m`, a SHA-256-pinned `template` image and a list of
anonymous `candidates`. Each candidate contains only `id`,
`range_m`, and a SHA-256-pinned `image` crop. A missing frame has
no candidates. The separate reference file holds `schema_version`,
`session_id` and `labels`, each with `request_id`,
`target_present` (boolean) and nullable `target_candidate_id`.
A present but unobserved target is represented by
`target_present=true, target_candidate_id=null`; an absent target
uses `target_present=false, target_candidate_id=null`.

**Identity isolation:** all image and range decisions for a session are
computed *before* opening its reference annotations. The evaluator checks
the labels only afterward. The same request is compared using normalized
pixel MAE (`image_mae`), range difference (`range_only`), and
equal-weight fusion (`image_range`), using existing selection and
abstention rules. Crop dimensions must match, and range readings are
**user-supplied values in metres**, not independently calibrated by this
reader.

The report includes failures, absent-target requests, wrong selections,
abstentions, session summaries and equally weighted family-level risk,
plus source/input hashes. Only `development` and `pilot` are
available: the CLI refuses `holdout` and does not read those files.
Source records never embed image pixels or raw reference annotations
in the output.

**Validity boundary:** a successful software replay verifies input
integrity and bookkeeping, *not* accuracy on real images, rights,
the identity of the measured objects, pose calibration, reference
independence or session independence. The data-origin and rights fields
are operator declarations, not certifications. Datasets stay outside
Git and GitHub Pages. This is an ingestion and evaluation interface;
the repository still has **no collected camera dataset** or physical
localization result. Clustering labels must reflect genuinely distinct
object families, not arbitrary renamed copies. No inferential interval
or confirmatory claim is computed.
