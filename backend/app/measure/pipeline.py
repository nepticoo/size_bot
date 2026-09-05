import cv2
import numpy as np

from app.measure.card import PX_PER_MM, find_card, is_blurry, rectify
from app.measure.ingest import load_upright_rgb
from app.measure.rules import RULES, WIDTH_RULES
from app.measure.segment import GarmentCropped, segment_garment


class Criterion:
    """Minimal shape pipeline needs from a MeasurementCriterion row —
    kept decoupled from SQLAlchemy so this module has no DB dependency."""

    def __init__(self, id: int, kind: str, measure_rule: str | None):
        self.id = id
        self.kind = kind
        self.measure_rule = measure_rule


def px_to_cm(px: float) -> float:
    return px / PX_PER_MM / 10


def run_pipeline_sync(photo_bytes: bytes, criteria: list[Criterion]) -> dict:
    """Photo -> {criterion_id: value_cm} or a rejection reason. Pure CPU work,
    safe to call from a worker thread (asyncio.to_thread)."""
    rgb = load_upright_rgb(photo_bytes)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # blur runs before card detection: a blurry photo also fails card detection,
    # so whichever check runs first decides the message the buyer sees (scenario 3)
    if is_blurry(gray):
        return {"status": "rejected", "reason": "blurry"}

    card_corners = find_card(bgr)
    if card_corners is None:
        return {"status": "rejected", "reason": "card_not_found"}

    rectified, card_rect = rectify(bgr, card_corners)

    try:
        mask = segment_garment(rectified, card_rect)
    except GarmentCropped:
        return {"status": "rejected", "reason": "garment_cropped"}

    values: dict[int, float] = {}
    for criterion in criteria:
        if not criterion.measure_rule or criterion.measure_rule not in RULES:
            continue
        raw_px = RULES[criterion.measure_rule](mask)
        value_cm = px_to_cm(raw_px)
        # a horizontal span across a laid-flat garment is half the circumference
        if criterion.kind == "circumference" and criterion.measure_rule in WIDTH_RULES:
            value_cm *= 2
        values[criterion.id] = round(value_cm, 1)

    return {"status": "measured", "values": values}
