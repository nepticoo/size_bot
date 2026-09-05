"""The twelve measure_rule implementations. Each takes a boolean garment mask
(y grows downward) and returns a raw pixel measurement — either a horizontal
span (for a *_width rule) or a vertical span (for a *_length / rise rule).
Pixel-to-cm conversion, and the circumference doubling for flat-lay spans,
happen in pipeline.py — these functions know nothing about scale or kind."""

import numpy as np


def _row_span(mask: np.ndarray, y: int) -> tuple[int, int] | None:
    row = mask[y]
    xs = np.where(row)[0]
    if xs.size == 0:
        return None
    return int(xs[0]), int(xs[-1])


def _row_width(mask: np.ndarray, y: int) -> int:
    span = _row_span(mask, y)
    return 0 if span is None else span[1] - span[0]


def _bounds(mask: np.ndarray) -> tuple[int, int]:
    ys = np.where(mask.any(axis=1))[0]
    return int(ys[0]), int(ys[-1])


def _width_profile(mask: np.ndarray, y0: int, y1: int) -> np.ndarray:
    return np.array([_row_width(mask, y) for y in range(y0, y1 + 1)])


def _find_armpit_row(mask: np.ndarray) -> int:
    """Deepest inward notch of the silhouette in the upper third: the row just
    below the shoulder/sleeve bulge where the width sharply narrows to the body."""
    top, bottom = _bounds(mask)
    height = bottom - top
    band_end = top + max(height // 3, 1)
    profile = _width_profile(mask, top, band_end)
    if profile.size < 3:
        return top
    peak = int(np.argmax(profile))
    # scan downward from the shoulder peak for the first local minimum
    notch = peak
    for i in range(peak + 1, profile.size - 1):
        if profile[i] <= profile[i + 1]:
            notch = i
            break
        notch = i
    return top + notch


def _find_crotch_row(mask: np.ndarray) -> int:
    """First row (scanning down from the waist) where the silhouette splits
    into two separate leg regions — the highest point of the inner notch."""
    top, bottom = _bounds(mask)
    for y in range(top, bottom + 1):
        row = mask[y]
        xs = np.where(row)[0]
        if xs.size == 0:
            continue
        gaps = np.where(np.diff(xs) > 1)[0]
        if gaps.size > 0:
            return y
    return bottom


def _leg_run(mask: np.ndarray, y: int, which: str = "left") -> tuple[int, int] | None:
    row = mask[y]
    xs = np.where(row)[0]
    if xs.size == 0:
        return None
    gaps = np.where(np.diff(xs) > 1)[0]
    if gaps.size == 0:
        return int(xs[0]), int(xs[-1])
    if which == "left":
        return int(xs[0]), int(xs[gaps[0]])
    return int(xs[gaps[-1] + 1]), int(xs[-1])


# ---- top garment rules ----------------------------------------------------


def chest_width(mask: np.ndarray) -> float:
    armpit = _find_armpit_row(mask)
    _, bottom = _bounds(mask)
    y = min(armpit + 10, bottom)  # ~1cm below the notch at typical phone resolution
    return float(_row_width(mask, y))


def garment_length(mask: np.ndarray) -> float:
    top, bottom = _bounds(mask)
    return float(bottom - top)


def shoulder_width(mask: np.ndarray) -> float:
    top, _ = _bounds(mask)
    return float(_row_width(mask, top + 2))


def sleeve_length(mask: np.ndarray) -> float:
    top, bottom = _bounds(mask)
    height = bottom - top
    band_end = top + max(height // 2, 1)
    # distance from the shoulder point to the farthest sleeve tip within the upper half
    shoulder_y = top
    shoulder_span = _row_span(mask, shoulder_y)
    if shoulder_span is None:
        return 0.0
    farthest = 0.0
    for y in range(top, band_end):
        span = _row_span(mask, y)
        if span is None:
            continue
        for x in span:
            for sx in shoulder_span:
                d = float(np.hypot(x - sx, y - shoulder_y))
                farthest = max(farthest, d)
    return farthest


def bicep_width(mask: np.ndarray) -> float:
    top, bottom = _bounds(mask)
    height = bottom - top
    band_start = top + max(height // 6, 1)
    band_end = top + max(height // 3, 1)
    profile = _width_profile(mask, band_start, band_end)
    return float(profile.max()) if profile.size else 0.0


def garment_waist_width(mask: np.ndarray) -> float:
    armpit = _find_armpit_row(mask)
    _, bottom = _bounds(mask)
    if bottom <= armpit:
        return 0.0
    profile = _width_profile(mask, armpit, bottom)
    return float(profile.min()) if profile.size else 0.0


# ---- bottom garment rules --------------------------------------------------


def waist_width(mask: np.ndarray) -> float:
    top, _ = _bounds(mask)
    return float(_row_width(mask, top + 1))


def bottom_length(mask: np.ndarray) -> float:
    top, bottom = _bounds(mask)
    return float(bottom - top)


def hip_width(mask: np.ndarray) -> float:
    top, bottom = _bounds(mask)
    height = bottom - top
    band_end = top + max(height // 3, 1)
    profile = _width_profile(mask, top, band_end)
    return float(profile.max()) if profile.size else 0.0


def thigh_width(mask: np.ndarray) -> float:
    crotch = _find_crotch_row(mask)
    _, bottom = _bounds(mask)
    y = min(crotch + 20, bottom)  # ~2cm below the crotch point
    run = _leg_run(mask, y, "left")
    return float(run[1] - run[0]) if run else 0.0


def leg_opening_width(mask: np.ndarray) -> float:
    _, bottom = _bounds(mask)
    run = _leg_run(mask, bottom - 1, "left")
    return float(run[1] - run[0]) if run else 0.0


def rise(mask: np.ndarray) -> float:
    top, _ = _bounds(mask)
    crotch = _find_crotch_row(mask)
    return float(crotch - top)


RULES = {
    "chest_width": chest_width,
    "garment_length": garment_length,
    "shoulder_width": shoulder_width,
    "sleeve_length": sleeve_length,
    "bicep_width": bicep_width,
    "garment_waist_width": garment_waist_width,
    "waist_width": waist_width,
    "bottom_length": bottom_length,
    "hip_width": hip_width,
    "thigh_width": thigh_width,
    "leg_opening_width": leg_opening_width,
    "rise": rise,
}

# rules that produce a horizontal span (subject to the circumference doubling
# in pipeline.py); the rest produce a vertical span, taken as-is.
WIDTH_RULES = {
    "chest_width",
    "shoulder_width",
    "bicep_width",
    "garment_waist_width",
    "waist_width",
    "hip_width",
    "thigh_width",
    "leg_opening_width",
}
