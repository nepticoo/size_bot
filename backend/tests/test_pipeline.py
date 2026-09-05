import asyncio
import io

import cv2
import numpy as np
from PIL import Image

from app.measure.pipeline import Criterion, run_pipeline_sync

CARD_RATIO_W, CARD_RATIO_H = 85.60, 53.98


def _encode_jpeg(bgr: np.ndarray) -> bytes:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def _scene_with_card_and_garment(card_scale=4.0, garment_box=(80, 250, 500, 550), border_gap=True):
    h, w = 900, 700
    canvas = np.full((h, w, 3), (235, 235, 235), dtype=np.uint8)
    if garment_box:
        x, y, gw, gh = garment_box
        cv2.rectangle(canvas, (x, y), (x + gw, y + gh), (160, 90, 40), -1)

    card_w = int(CARD_RATIO_W * card_scale)
    card_h = int(CARD_RATIO_H * card_scale)
    cx, cy = 100, 90
    cv2.rectangle(canvas, (cx, cy), (cx + card_w, cy + card_h), (20, 20, 20), -1)
    return canvas


def _sharpen_texture(canvas):
    # add a crisp checkerboard so edges are sharp (defeats the blur check)
    # without perturbing large flat regions enough to confuse segmentation
    out = canvas.copy()
    step = 6
    for y in range(0, canvas.shape[0], step):
        out[y : y + 1, :] = np.clip(out[y : y + 1, :].astype(np.int16) + 15, 0, 255).astype(np.uint8)
    return out


def test_blurry_photo_rejected_before_card_check():
    canvas = _scene_with_card_and_garment()
    blurred = cv2.GaussianBlur(canvas, (31, 31), 0)
    data = _encode_jpeg(blurred)
    result = run_pipeline_sync(data, [])
    assert result == {"status": "rejected", "reason": "blurry"}


def test_no_card_rejected():
    canvas = np.full((900, 700, 3), (235, 235, 235), dtype=np.uint8)
    canvas = _sharpen_texture(canvas)
    cv2.rectangle(canvas, (80, 250), (580, 800), (160, 90, 40), -1)
    data = _encode_jpeg(canvas)
    result = run_pipeline_sync(data, [])
    assert result == {"status": "rejected", "reason": "card_not_found"}


def test_garment_touching_border_rejected():
    # garment touches the left edge; card is drawn afterwards so it stays intact
    canvas = _scene_with_card_and_garment(garment_box=(0, 250, 500, 550))
    canvas = _sharpen_texture(canvas)
    data = _encode_jpeg(canvas)
    result = run_pipeline_sync(data, [])
    assert result["status"] == "rejected"
    assert result["reason"] == "garment_cropped"


def test_measured_returns_values_for_known_criteria():
    canvas = _scene_with_card_and_garment()
    canvas = _sharpen_texture(canvas)
    data = _encode_jpeg(canvas)
    criteria = [Criterion(id=1, kind="length", measure_rule="garment_length")]
    result = run_pipeline_sync(data, criteria)
    assert result["status"] == "measured"
    assert 1 in result["values"]
    assert result["values"][1] > 0


def test_two_uploads_run_concurrently_without_blocking():
    async def main():
        canvas = _scene_with_card_and_garment()
        canvas = _sharpen_texture(canvas)
        data = _encode_jpeg(canvas)
        criteria = [Criterion(id=1, kind="length", measure_rule="garment_length")]
        results = await asyncio.gather(
            asyncio.to_thread(run_pipeline_sync, data, criteria),
            asyncio.to_thread(run_pipeline_sync, data, criteria),
        )
        return results

    results = asyncio.run(main())
    assert all(r["status"] == "measured" for r in results)
