import cv2
import numpy as np
import pytest

from app.measure.segment import GarmentCropped, segment_garment


def _scene(garment_box, canvas_size=(500, 700), bg_color=(235, 235, 235), fg_color=(40, 90, 160)):
    h, w = canvas_size
    canvas = np.full((h, w, 3), bg_color, dtype=np.uint8)
    x, y, gw, gh = garment_box
    cv2.rectangle(canvas, (x, y), (x + gw, y + gh), fg_color, -1)
    return canvas


def test_segments_garment_excluding_card():
    canvas = _scene((150, 100, 300, 350))
    card_rect = (160, 110, 80, 50)  # sits inside the garment box
    mask = segment_garment(canvas, card_rect)
    assert mask.any()
    # card area should not be counted as garment
    cx, cy, cw, ch = card_rect
    assert not mask[cy + ch // 2, cx + cw // 2]
    # a point clearly inside the garment (away from the card) should be foreground
    assert mask[400, 300]


def test_cropped_garment_is_rejected():
    h, w = 500, 700
    canvas = np.full((h, w, 3), (235, 235, 235), dtype=np.uint8)
    # garment runs off the left edge entirely
    cv2.rectangle(canvas, (0, 100), (300, 400), (40, 90, 160), -1)
    with pytest.raises(GarmentCropped):
        segment_garment(canvas, (0, 0, 1, 1))
