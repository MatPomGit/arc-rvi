"""Small planar geometric operations in metres and radians."""

from math import hypot, isfinite, pi, remainder


def angular_distance(first: float, second: float) -> float:
    return abs(remainder(first - second, 2 * pi))


def segment_distance(
    point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]
) -> float:
    """Euclidean distance to the closed segment, including its endpoints."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = hypot(dx, dy)
    if not isfinite(length):
        raise ValueError("geometry exceeds finite distance range")
    if length == 0:
        result = hypot(point[0] - start[0], point[1] - start[1])
    else:
        ux, uy = dx / length, dy / length
        projection = (point[0] - start[0]) * ux + (point[1] - start[1]) * uy
        if not isfinite(projection):
            raise ValueError("geometry exceeds finite projection range")
        projection = max(0.0, min(length, projection))
        result = hypot(point[0] - (start[0] + projection * ux),
                       point[1] - (start[1] + projection * uy))
    if not isfinite(result):
        raise ValueError("geometry exceeds finite distance range")
    return result
