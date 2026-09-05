import io

import numpy as np
import pillow_heif
from PIL import Image

from app.measure.ingest import load_upright_rgb


def _make_test_image(w=300, h=200) -> Image.Image:
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, : w // 2] = (255, 0, 0)  # left half red
    arr[:, w // 2 :] = (0, 255, 0)  # right half green
    return Image.fromarray(arr)


def test_rotated_jpeg_comes_out_upright():
    img = _make_test_image(300, 200)
    buf = io.BytesIO()
    # EXIF orientation 6 = rotate 90 CW needed to display upright,
    # i.e. the stored pixels are rotated 90 CCW relative to intended display.
    exif = img.getexif()
    exif[0x0112] = 6
    img.save(buf, format="JPEG", exif=exif)
    data = buf.getvalue()

    result = load_upright_rgb(data)
    # orientation 6 means the stored 300x200 pixels must be rotated 90 degrees
    # to display upright, so the corrected array comes out portrait (200x300)
    assert result.shape[0] == 300 and result.shape[1] == 200


def test_heic_upload_decodes():
    img = _make_test_image(300, 200)
    heif = pillow_heif.from_pillow(img)
    buf = io.BytesIO()
    heif.save(buf, format="HEIF")
    data = buf.getvalue()

    result = load_upright_rgb(data)
    assert result.shape[2] == 3
    assert result.shape[0] > 0 and result.shape[1] > 0


def test_downscale_long_edge():
    img = _make_test_image(3000, 1500)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    result = load_upright_rgb(buf.getvalue())
    assert max(result.shape[0], result.shape[1]) <= 2000
