"""Tiny synthetic 8x8 grayscale patches; not natural camera images.

The simulator knows template ownership while generating anonymous observations;
the selector receives only pixel arrays and numeric cues.
"""
from __future__ import annotations

from hashlib import sha256
import json
from random import Random

SIDE = 8
PIXELS = SIDE * SIDE


def _stream(*parts: object) -> Random:
    raw = json.dumps(parts, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return Random(int.from_bytes(sha256(raw).digest()[:8], "big"))


def validate_pixels(values: object) -> tuple[int, ...]:
    """Require exactly 64 finite uint8 samples; reject booleans and floats."""
    if (not isinstance(values, (list, tuple)) or len(values) != PIXELS
            or any(type(v) is not int or not 0 <= v <= 255 for v in values)):
        raise ValueError("grayscale patch must contain 64 uint8 pixels")
    return tuple(values)


def texture_templates(seed: int, family: str, similarity: str) -> dict[str, list[int]]:
    """Draw image textures once per family (all sessions reuse the identity)."""
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("texture seed must be unsigned 64-bit integer")
    if type(family) is not str or not family:
        raise ValueError("family must be a nonempty string")
    if similarity not in ("similar", "distinct"):
        raise ValueError("similarity must be similar or distinct")
    rng = _stream("rvi-grayscale-v1", seed, family)
    target = [rng.choice((56, 200)) for _ in range(PIXELS)]
    distractor = target.copy()
    indices = list(range(PIXELS))
    rng.shuffle(indices)
    for idx in indices[:(4 if similarity == "similar" else 40)]:
        distractor[idx] = 256 - distractor[idx]
    # Absent-request template is a different object, not a copied distractor.
    absent = [rng.choice((56, 200)) for _ in range(PIXELS)]
    return {"target": target, "distractor": distractor, "absent": absent}


def render_patch(
    template: object, seed: int, session_id: str, frame_index: int,
    identity: str,
) -> list[int]:
    """Correlated per-session luminance bias plus frame-local sensor noise."""
    values = validate_pixels(template)
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("noise seed must be unsigned 64-bit integer")
    if type(session_id) is not str or not session_id:
        raise ValueError("session id must be a nonempty string")
    if type(identity) is not str or not identity:
        raise ValueError("identity must be a nonempty string")
    if type(frame_index) is not int or not 0 <= frame_index < 2**32:
        raise ValueError("frame index must be unsigned 32-bit integer")
    bias = _stream("rvi-grayscale-session-v1", seed, session_id).randint(-6, 6)
    rng = _stream("rvi-grayscale-frame-v1", seed, session_id, frame_index, identity)
    return [max(0, min(255, px + bias + rng.randint(-5, 5))) for px in values]


def pixel_distance(reference: object, observed: object) -> float:
    """Mean absolute error normalized to [0,1], independent of geometry."""
    a, b = validate_pixels(reference), validate_pixels(observed)
    return sum(abs(x - y) for x, y in zip(a, b)) / (PIXELS * 255)
