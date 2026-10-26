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

The planned fixture-level API accepts **precomputed, normalized distances**
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
   and a no-reference-leakage boundary. This is **not implemented**.
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
