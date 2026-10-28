"""Offline *observed-pixel* photometric proxies for annotated car/part images.

No automated vehicle recognition, defect detection, physical HDR calibration,
robot control or claim of independent inspection validity is provided.
Images and masks remain local and are only read. The reviewer supplies
source-pinned ROI annotations and thresholds, not the planning controller.
"""
from __future__ import annotations

import hashlib
import io
import math
from pathlib import Path, PurePosixPath
import re
import warnings

MAX_BYTES = 24 * 1024 * 1024
MAX_PIXELS = 8_000_000
_HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _str(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label}: nonempty string required")
    return value


def _unit(value: object, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label}: finite fraction in [0,1] required")
    return float(value)


def _byte(value: object, label: str) -> int:
    if type(value) is not int or not 0 <= value <= 255:
        raise ValueError(f"{label}: integer 0..255 required")
    return value


def _file_and_hash(root: Path, entry: object, label: str) -> tuple[Path, bytes, str]:
    if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
        raise ValueError(f"{label}: path and sha256 required")
    relative = PurePosixPath(_str(entry["path"], f"{label}.path"))
    if relative.is_absolute() or not relative.parts or any(p in ("..", ".") for p in relative.parts):
        raise ValueError(f"{label}: relative path without traversal required")
    expected = _str(entry["sha256"], f"{label}.sha256")
    if not _HEX_SHA.fullmatch(expected):
        raise ValueError(f"{label}: lowercase SHA256 required")
    base = root.resolve(strict=True)
    file = base
    for part in relative.parts:
        file = file / part
        if file.is_symlink():
            raise ValueError(f"{label}: symlink paths are forbidden")
    file = file.resolve(strict=True)
    if not file.is_relative_to(base) or not file.is_file() or file.stat().st_size > MAX_BYTES:
        raise ValueError(f"{label}: invalid, external or oversized file")
    data = file.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise ValueError(f"{label}: SHA256 mismatch")
    return file, data, digest


def _token(data: bytes, position: int) -> tuple[bytes, int]:
    length = len(data)
    while position < length:
        if data[position] in b" \t\r\n":
            position += 1
        elif data[position] == 35:  # Header comment, never binary pixels
            end = data.find(b"\n", position)
            if end < 0:
                raise ValueError("Netpbm header has unterminated comment")
            position = end + 1
        else:
            break
    start = position
    while position < length and data[position] not in b" \t\r\n#":
        position += 1
    if start == position:
        raise ValueError("malformed or incomplete Netpbm header")
    return data[start:position], position


def _netpbm(data: bytes, *, mask: bool) -> tuple[int, int, bytes]:
    """P2/P3 (ASCII) and P5/P6 (8-bit binary); fixed-size bounded parsing."""
    pos = 0
    mode, pos = _token(data, pos)
    if mode not in ((b"P2", b"P5") if mask else (b"P2", b"P3", b"P5", b"P6")):
        raise ValueError("unsupported Netpbm image/mask encoding")
    tokens = []
    for _ in range(3):
        item, pos = _token(data, pos)
        if not item.isascii() or not item.isdigit():
            raise ValueError("invalid Netpbm dimensions or maxval")
        tokens.append(int(item))
    width, height, maxval = tokens
    if not (0 < width <= MAX_PIXELS and 0 < height <= MAX_PIXELS
            and width * height <= MAX_PIXELS and 1 <= maxval <= 255):
        raise ValueError("unsupported Netpbm dimensions/maxval")
    count = width * height * (3 if mode in (b"P3", b"P6") else 1)
    if mode in (b"P5", b"P6"):
        if maxval != 255:
            raise ValueError("binary Netpbm maxval must be 255")
        if pos >= len(data) or data[pos] not in b" \t\r\n":
            raise ValueError("missing Netpbm raster separator")
        # One separator; CRLF is a single logical separator. Do not skip pixels!
        pos += 2 if data[pos:pos+2] == b"\r\n" else 1
        raw = data[pos:]
        if len(raw) != count:
            raise ValueError("Netpbm binary raster size mismatch")
    else:
        values = []
        for _ in range(count):
            item, pos = _token(data, pos)
            if not item.isascii() or not item.isdigit():
                raise ValueError("invalid ASCII Netpbm sample")
            n = int(item)
            if n > maxval:
                raise ValueError("sample exceeds Netpbm maxval")
            values.append(round(n * 255 / maxval))
        if data[pos:].strip():
            raise ValueError("trailing ASCII Netpbm data")
        raw = bytes(values)
    if mode in (b"P2", b"P5") and not mask:
        rgb = bytearray(width * height * 3)
        for i, v in enumerate(raw):
            rgb[3*i:3*i+3] = bytes((v, v, v))
        raw = bytes(rgb)
    return width, height, raw


def _load_pixels(path: Path, data: bytes, *, mask: bool) -> tuple[int, int, bytes]:
    suffix = path.suffix.lower()
    if suffix in (".pgm", ".ppm", ".pnm"):
        return _netpbm(data, mask=mask)
    if suffix not in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"):
        raise ValueError("image format unsupported")
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise ValueError("Pillow is required for PNG/JPEG/WEBP/TIFF; no auto-install") from exc
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(data)) as image:
                if image.width * image.height > MAX_PIXELS:
                    raise ValueError("image exceeds pixel bound")
                image = ImageOps.exif_transpose(image)
                image = image.convert("L" if mask else "RGB")
                width, height = image.size
                pixels = image.tobytes()
        except (OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            raise ValueError("cannot decode bounded image") from exc
    return width, height, pixels


def analyze_capture(spec: dict, data_root: Path) -> dict:
    """Report *observed* clipping/brightness proxies inside an annotated ROI.

    A metric pass is NOT independent defect visibility, correctly recognized
    car/part identity, verified calibration, or a completed photo mission.
    """
    if not isinstance(spec, dict) or spec.get("schema_version") != 1:
        raise ValueError("unsupported capture schema")
    association = spec.get("association")
    if not isinstance(association, dict):
        raise ValueError("association object required")
    for key in ("vehicle_instance_id", "part_label", "slot_id",
                "observation_id", "annotation_id", "annotation_origin"):
        _str(association.get(key), f"association.{key}")
    image_file, image_bytes, image_sha = _file_and_hash(
        data_root, spec.get("image"), "image")
    mask_file, mask_bytes, mask_sha = _file_and_hash(
        data_root, spec.get("roi_mask"), "roi_mask")
    iw, ih, rgb = _load_pixels(image_file, image_bytes, mask=False)
    mw, mh, region = _load_pixels(mask_file, mask_bytes, mask=True)
    if (iw, ih) != (mw, mh):
        raise ValueError("image and independent ROI-mask dimensions disagree")
    if len(rgb) != iw * ih * 3 or len(region) != iw * ih:
        raise ValueError("decoded raster dimension mismatch")
    policy = spec.get("photometric_policy")
    if not isinstance(policy, dict):
        raise ValueError("photometric_policy object required")
    clip_threshold = _byte(policy.get("white_channel_clip_threshold"),
                           "white_channel_clip_threshold")
    bright_threshold = _byte(policy.get("bright_luma_threshold"),
                             "bright_luma_threshold")
    neutral_spread = _byte(policy.get("neutral_channel_spread_max"),
                           "neutral_channel_spread_max")
    dark_threshold = _byte(policy.get("dark_luma_threshold"),
                           "dark_luma_threshold")
    max_white = _unit(policy.get("max_white_clipped_fraction"),
                      "max_white_clipped_fraction")
    max_bright = _unit(policy.get("max_bright_neutral_fraction"),
                       "max_bright_neutral_fraction")
    max_dark = _unit(policy.get("max_dark_fraction"), "max_dark_fraction")
    min_pixels = policy.get("min_roi_pixels")
    if type(min_pixels) is not int or min_pixels < 1 or min_pixels > MAX_PIXELS:
        raise ValueError("min_roi_pixels must be positive bounded integer")
    count = white_clip = any_clip = bright_neutral = dark = 0
    for i, included in enumerate(region):
        if not included:
            continue
        count += 1
        r, g, b = rgb[i*3:i*3+3]
        luminance = (77*r + 150*g + 29*b) // 256
        if min(r, g, b) >= clip_threshold:
            white_clip += 1
        if max(r, g, b) >= clip_threshold:
            any_clip += 1
        if luminance >= bright_threshold and max(r, g, b)-min(r, g, b) <= neutral_spread:
            bright_neutral += 1
        if luminance <= dark_threshold:
            dark += 1
    if count == 0:
        raise ValueError("ROI mask empty")
    white_fraction = white_clip/count
    bright_fraction = bright_neutral/count
    dark_fraction = dark/count
    reasons = []
    if count < min_pixels:
        reasons.append("roi_under_minimum_pixel_count")
    if white_fraction > max_white:
        reasons.append("white_channel_clipping_proxy")
    if bright_fraction > max_bright:
        reasons.append("bright_neutral_highlight_proxy")
    if dark_fraction > max_dark:
        reasons.append("dark_pixel_fraction")
    return {
        "schema_version": 1,
        "image_sha256": image_sha,
        "roi_mask_sha256": mask_sha,
        "association": association.copy(),
        "roi_pixels": count,
        "roi_fraction_of_frame": count/(iw*ih),
        "image_width_px": iw,
        "image_height_px": ih,
        "metrics": {
            "white_clipped_fraction": white_fraction,
            "any_channel_clipped_fraction_diagnostic_only": any_clip/count,
            "bright_neutral_fraction": bright_fraction,
            "dark_fraction": dark_fraction,
        },
        "gate": "photometric_proxy_pass" if not reasons else "photometric_proxy_reject",
        "reasons": reasons,
        "focus_and_defect_visibility": "not_assessed",
        "vehicle_and_part_identity": "declared_annotation_only_not_model_verified",
        "independent_image_quality": "not_certified",
        "physical_robot_evidence": False,
    }


def compare_pair(before: dict, after: dict, root: Path) -> dict:
    """Descriptive same-slot before/after comparison, never infer treatment effects."""
    a = analyze_capture(before, root)
    b = analyze_capture(after, root)
    for field in ("vehicle_instance_id", "part_label", "slot_id"):
        if a["association"][field] != b["association"][field]:
            raise ValueError(f"paired captures differ in {field}")
    if a["image_sha256"] == b["image_sha256"]:
        raise ValueError("paired captures share the same image bytes")
    keys = ("white_clipped_fraction", "bright_neutral_fraction", "dark_fraction")
    return {
        "pair_key": {
            field: a["association"][field]
            for field in ("vehicle_instance_id", "part_label", "slot_id")
        },
        "before": a,
        "after": b,
        "after_minus_before": {
            key: b["metrics"][key] - a["metrics"][key] for key in keys
        },
        "evidence_class": "descriptive_offline_image_proxy_only",
        "calibrated_specular_reflection": False,
        "causal_recovery_effect": False,
    }
