"""Quality decision from already measured image features.

Actual feature extraction from camera images is deliberately not implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class QualityLimits:
    sharpness_min: float
    exposure_min: float
    exposure_max: float

    def __post_init__(self) -> None:
        values = (self.sharpness_min, self.exposure_min, self.exposure_max)
        if not all(isfinite(x) for x in values):
            raise ValueError("limits must be finite")
        if self.sharpness_min < 0 or not (0 <= self.exposure_min < self.exposure_max <= 255):
            raise ValueError("invalid limits")


def accept_measurements(
    sharpness: float, exposure_mean: float, limits: QualityLimits
) -> bool:
    if not isfinite(sharpness) or not isfinite(exposure_mean):
        return False
    return (
        sharpness >= limits.sharpness_min
        and limits.exposure_min <= exposure_mean <= limits.exposure_max
    )
