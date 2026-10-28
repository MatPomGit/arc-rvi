# Vehicle bodywork image QA: observed ROI proxies

**Version:** 1.0.0 · 2026-10-28 · **Status:** implemented read-only
offline image ingestion and observed-pixel QA, **not** autonomous visual
recognition or a calibrated specularity/defect-validity detector.

## Why this component exists

In the commanded inspection scenario, a polished car surface may
reflect the sun, a lamp, a building or the robot. Evaluating global
exposure is inadequate: a white sky can be fully saturated while the
annotated bumper is readable, or the rest of the image can be exposed
well while the required bumper area is blown out.

The [ROI assessor](https://github.com/MatPomGit/arc-rvi/blob/main/src/rvi/vehicle_image_quality.py)
reads an **actual image raster** together with a separately supplied
**target-part mask**, verifies both file hashes and reports how many
pixels *inside the mask* meet simple clipping/brightness tests. Files
remain local and are not uploaded.

The mask is supplied by an independent annotation workflow or
eventually a separately validated segmentation model. Merely providing
a mask and a \`vehicle_instance_id\` **does not demonstrate** that
ARC-RVI identified the correct car or bumper. The current module
neither recognizes cars nor estimates camera pose.

## API and reproducible example

Run from the project root:

\`\`\`bash
python scripts/audit_vehicle_image_roi.py \
  --manifest simulation/suites/vehicle_roi_synthetic_pair.json \
  --data-root simulation/suites
\`\`\`

The committed P3/P2 Netpbm images are **synthetic pixels**, not
photographs. The initial bumper ROI contains three white pixels of
four and the second ROI zero, while the bright background is the
same. The pair demonstrates source-hashed masking and reports
\`after_minus_before\`, **not** a physical intervention effect.

A local manifest uses \`mode: single\` with a \`capture\` object, or
\`mode: pair\` with \`before\` and \`after\` objects. Each capture has:
\`schema_version: 1\`; image and mask
\`{path: relative_path, sha256: 64_lowercase_hex}\`; an \`association\`
object with \`vehicle_instance_id\`, \`part_label\`, \`slot_id\`,
\`observation_id\`, \`annotation_id\` and \`annotation_origin\`;
and the same \`photometric_policy\` thresholds across matched pairs.

The eight quality-policy fields are:
\`white_channel_clip_threshold\` (0–255),
\`bright_luma_threshold\` (0–255),
\`neutral_channel_spread_max\` (0–255),
\`dark_luma_threshold\` (0–255),
\`max_white_clipped_fraction\` (0–1),
\`max_bright_neutral_fraction\` (0–1),
\`max_dark_fraction\` (0–1) and \`min_roi_pixels\` (integer).

**Formats:** ASCII/binary 8-bit Netpbm P2/P3/P5/P6 are read with
the Python standard library. PNG, JPEG, WebP and TIFF are supported
when the *optional, free* Pillow package is already installed.
There is **no automatic installation**. EXIF orientation is applied
before analysing compressed formats; mask dimensions must match the
oriented image. Images are capped at 8 million pixels and 24 MiB of
input bytes per file. Source paths cannot leave the data root or
use symlinks.

## Metrics, and what they do not mean

| Metric within nonzero mask pixels | Definition | Interpretation limit |
| --- | --- | --- |
| \`white_clipped_fraction\` | Fraction of pixels for which **all three** RGB channels exceed declared threshold | Candidate saturated white ROI; may also be legitimate white paint or lighting |
| \`any_channel_clipped_fraction_diagnostic_only\` | Fraction with at least one high RGB channel | **Not used to reject**: red/yellow car paint can naturally saturate one channel |
| \`bright_neutral_fraction\` | High 8-bit weighted RGB luminance with low RGB channel spread | **Highlight proxy**, not proof of specular BRDF response |
| \`dark_fraction\` | Low weighted RGB luminance fraction | Underexposure proxy, sensitive to inherently dark paint and shadows |

Output \`gate=photometric_proxy_pass\` means **only** that declared
photometric thresholds passed on the *supplied* mask. It does **not**
mean that the correct car or component was located, a defect is visible,
focus and motion blur are adequate, exposure is calibrated, or the
assigned shot can be accepted as inspection evidence. Output therefore
retains \`focus_and_defect_visibility=not_assessed\`,
\`vehicle_and_part_identity=declared_annotation_only_not_model_verified\`,
\`independent_image_quality=not_certified\` and
\`physical_robot_evidence=false\`. Do **not** feed
\`photometric_proxy_pass\` directly into the whole-mission
\`independent_qc\` boolean or autonomous walking/camera control.

A pair is permitted only for the **same declared vehicle, part and shot
slot**, with different image hashes. Paired deltas are descriptive; there
is no randomization, calibrated reflectance model or causal estimate.

## Validation needed before scientific or robotic use

1. Independently annotate target car and part masks and identify the
   original physical object; record camera model, RAW/JPEG processing,
   exposure, polarization, illumination, distances, lens distortions,
   mask inter-rater agreement and correct image-to-object binding.
2. Define defect/inspection-acceptance by blinded human assessors
   separately from this image-proxy algorithm and lock operational
   thresholds on **development-only** vehicle and lighting sessions.
3. Compare ROI proxy decisions with true specular masking or calibrated
   HDR/RAW measurements and independently assessed defect visibility.
   Analyse false accepts, false rejects and operator-annotator differences
   by paint colour, body curvature, lighting and material. A bright white
   vehicle is a crucial negative control for a naive bright-highlight proxy.
4. Freeze independent **vehicle and acquisition-session** splits,
   include car-absent and incorrect-bumper cases, and retain all
   failed/no-image attempts and reacquisitions. Use grouped confidence
   intervals; frames from the same car are not independent samples.
5. Compare camera reorientation to same-view retries and exposure
   adjustments at common **mission time**, safe viewpoint limits and
   human-return reserves. A lower measured clipping fraction by itself
   does not prove the photograph is better for inspection.
6. Only after actual G1 EDU optical calibration, verified hardware
   safety gates and source-to-image metadata integration may this become
   one input to an authorised physical evidence workflow.

Related work: [vehicle mission](vehicle-inspection-missions.md),
[P02 association and abstention](localization.md),
[P06 quality protocol](../experiments/exp06_quality_control/protocol.md),
[P07 sim-to-real protocol](../experiments/exp07_transfer/protocol.md),
and [core image data interface](data-interface.md).
