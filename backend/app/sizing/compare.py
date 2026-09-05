"""Fit bands, recommendation and notes. All the tunable numbers below come
from docs/versions/0.1/13-questions.md's defaults, written into
architecture.md — the founder can change these four numbers later without
any redesign, so keep them as named constants, not scattered literals."""

from dataclasses import dataclass, field

# fit bands over d_circ = size - buyer, in cm
BAND_VERY_TIGHT_MAX = -6
BAND_TIGHT_MAX = -2
BAND_SAME_MAX = 3
BAND_LOOSE_MAX = 8

# no size fits when the best d_circ falls outside this range
NO_FIT_LOW = -6
NO_FIT_HIGH = 12

# mandatory length note threshold
LENGTH_NOTE_THRESHOLD = 1.5

# secondary note thresholds and cap
SECONDARY_LENGTH_THRESHOLD = 2.0
SECONDARY_CIRCUMFERENCE_THRESHOLD = 4.0
MAX_SECONDARY_NOTES = 2


@dataclass
class CriterionInfo:
    id: int
    name: str
    kind: str  # circumference | length
    is_main: bool


@dataclass
class SizeChart:
    id: int
    name: str
    values: dict[int, float] = field(default_factory=dict)  # criterion_id -> normalised cm


def fit_word(d_circ: float) -> str:
    if d_circ < BAND_VERY_TIGHT_MAX:
        return "خیلی تنگ‌تر از لباسِ خودت"
    if d_circ < BAND_TIGHT_MAX:
        return "تنگ‌تر از لباسِ خودت"
    if d_circ <= BAND_SAME_MAX:
        return "مثلِ لباسِ خودت"
    if d_circ <= BAND_LOOSE_MAX:
        return "کمی آزادتر"
    return "آزاد"


def compute_answer(
    buyer_values: dict[int, float],
    sizes: list[SizeChart],
    criteria: list[CriterionInfo],
) -> dict:
    main_criteria = [c for c in criteria if c.is_main]
    main_ids = {c.id for c in main_criteria}
    circ_main = next((c for c in main_criteria if c.kind == "circumference"), None)
    len_main = next((c for c in main_criteria if c.kind == "length"), None)

    complete_sizes = [s for s in sizes if main_ids.issubset(s.values.keys())]

    if circ_main is None or not complete_sizes or circ_main.id not in buyer_values:
        return {"status": "no_sizes"}

    buyer_circ = buyer_values[circ_main.id]
    buyer_len = buyer_values.get(len_main.id) if len_main else None

    diffs = [(s, s.values[circ_main.id] - buyer_circ) for s in complete_sizes]
    best_abs = min(abs(d) for _, d in diffs)
    tied = [(s, d) for s, d in diffs if abs(d) - best_abs < 1e-9]
    # on a tie, prefer the larger size (decision: circumference decides, always)
    best_size, best_d = max(tied, key=lambda sd: sd[0].values[circ_main.id])

    all_sizes_out = [
        {"id": s.id, "name": s.name, "fit_word": fit_word(d), "is_recommended": s.id == best_size.id}
        for s, d in diffs
    ]

    if best_d < NO_FIT_LOW or best_d > NO_FIT_HIGH:
        return {
            "status": "no_fit",
            "nearest_size": {"id": best_size.id, "name": best_size.name},
            "nearest_direction": "tight" if best_d < 0 else "loose",
            "sizes": all_sizes_out,
        }

    length_note = None
    if len_main is not None and buyer_len is not None and len_main.id in best_size.values:
        d_len = best_size.values[len_main.id] - buyer_len
        if abs(d_len) > LENGTH_NOTE_THRESHOLD:
            if d_len > 0:
                length_note = "قدش کمی بلندتر از لباسی است که فرستادی."
            else:
                length_note = "قدش کمی کوتاه‌تر از لباسی است که فرستادی."

    secondary = []
    for c in criteria:
        if c.is_main or c.id not in buyer_values or c.id not in best_size.values:
            continue
        diff = best_size.values[c.id] - buyer_values[c.id]
        threshold = (
            SECONDARY_CIRCUMFERENCE_THRESHOLD if c.kind == "circumference" else SECONDARY_LENGTH_THRESHOLD
        )
        if abs(diff) > threshold:
            secondary.append((abs(diff), c.name, diff))

    secondary.sort(key=lambda t: t[0], reverse=True)
    secondary_notes = [
        f"{name} کمی {'بیشتر' if diff > 0 else 'کمتر'} از لباسی است که فرستادی."
        for _, name, diff in secondary[:MAX_SECONDARY_NOTES]
    ]

    return {
        "status": "answered",
        "recommended_size": {"id": best_size.id, "name": best_size.name},
        "sizes": all_sizes_out,
        "length_note": length_note,
        "secondary_notes": secondary_notes,
    }
