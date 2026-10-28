# Car colour cues from annotated photographs

**Version:** 1.0.0 · 2026-10-28 · **Evidence:** offline pixel-feature
pilot, not detection, identification, instruction grounding or physical
robot deployment.

## Research motivation

If the human says *"Photograph the red car"*, colour can be one
observable clue. The robot must still localise candidate cars and link
the words to a **specific instance**, not treat the highest colour
score as the correct target. With two red cars, colour is insufficient.
If someone says *"the bumper of that one"*, identification requires
temporal, pointing, context or explicit human clarification and
a **part-to-parent** spatial association after vehicle selection.

The existing [mission contract](vehicle-inspection-missions.md)
enforces human disambiguation and reference-image quality. This small
colour-cue baseline fills one lower-level image-feature gap: it
evaluates **observed RGB pixels** rather than assuming synthetic
\`matches_description\` flags. Its inputs nevertheless contain
**externally drawn/provided car body masks**; it neither detects cars
nor segments bumpers.

## Read-only workflow

Run the bundled *synthetic scene* (four pixels per car):

\`\`\`bash
python scripts/propose_vehicle_colour_targets.py \
  --manifest simulation/suites/vehicle_colour_two_cars_manifest.json \
  --data-root simulation/suites
\`\`\`

The source-hashed ASCII P3 image and two P2 car masks are a
**software fixture**, not real car photographs. The left shape is
uniformly red and the right uniformly blue. The output proposes
\`synthetic-left-car\` only, but returns
\`identity_confirmed=false\` and
\`safe_to_start_physical_inspection=false\`.

For local photographs, supply a JSON manifest with:
\`schema_version=1\`, image \`path\`/\`sha256\`,
\`request={utterance_id, observation_frame_id, requested_colour}\`,
\`policy\`, and candidates with
\`vehicle_instance_id\`, \`mask_annotation_id\`,
\`annotation_origin\` and a per-candidate
\`car_body_mask={path, sha256}\`. All assets must remain under the
specified local data root without symlink traversal. The same
eight-megapixel/24 MiB bounds and optional Pillow decoder as
[image QA](vehicle-image-qa.md) apply.

### Fixed, uncalibrated pixel rule

Currently only \`red\`, \`blue\`, \`green\`, \`yellow\` are supported
as *explicit semantic tokens* extracted upstream. This is not
ASR or free-text language understanding.

For each externally identified car-mask pixel, ignore pixels with
very low RGB chroma or outside the declared intensity interval.
This excludes many grey specular highlights and shadows, but can
also discard meaningful pixels. Among remaining usable pixels, use
a fixed channel-dominance heuristic. The supplied manifest defines
\`minimum_chroma\`, \`minimum_intensity\`,
\`maximum_intensity\`, \`minimum_mask_pixels\`,
\`minimum_usable_fraction\` and
\`minimum_matching_fraction\` before any evaluation.

A car is only a *candidate colour hint* when its masked usable
fraction and matching-colour fraction both meet the declared
thresholds. If two cars pass, status is
\`ambiguous_multiple_colour_candidates\`. If one passes, status
is \`single_unverified_colour_candidate\`. If none pass,
\`no_supported_colour_candidate\` **does not prove the requested car
is physically absent**, only that this weak cue cannot support it.

The method is deliberately weak for metallic silver, white, black,
multi-colour, colour-shifting, strongly shadowed, overexposed or
occluded cars, and for illumination/camera white-balance shifts.
It does not estimate a colour posterior, re-identification embedding
or identity confidence. A wrong, overlapping or stale input mask can
produce a spurious colour match.

## Validation gates before attempting autonomous grounding

1. Record original human utterance, time, language, demonstratives,
   reference frame and number of plausible candidate cars.
2. Use independently checked car-instance masks and retained
   associations across frames. Distinct car masks and part masks
   must carry parent vehicle identifiers and acquisition timestamps.
3. Compare this colour baseline to geometry-only, appearance-only,
   combined appearance/geometry and explicit human clarification
   on **independent vehicle models and acquisition sessions**.
4. Measure wrong-car selection, correct target selection, abstention,
   ambiguity resolution and not-found cases. Always-abstain is not
   success. Tune all confidence thresholds only on development data.
5. Include non-red/blue, two matching vehicles, unseen paint and
   illumination, reflected sunlight, garage lamps, glass and chrome,
   near-identical vehicles, occluded number plates and no target.
6. Do not promote the pixel-cue result to
   \`target_grounding.decision.status=resolved\` without independent
   referential/identity evidence and the required operator
   clarification. All physical G1 EDU operation still requires
   verified robot integration and separate safety approval.

Scientific interpretation: a deterministic **colour-feature**
development baseline for P02, not a novel vision-language model,
and not evidence that the integrated humanoid mission works.
See [P02 protocol](../experiments/exp02_localization/protocol.md),
[physical safety gates](safety.md) and
[reproducible data contract](reproducibility.md).
