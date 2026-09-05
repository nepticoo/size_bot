import io

import numpy as np
import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_LONG_EDGE = 2000


class UploadTooLarge(Exception):
    pass


def load_upright_rgb(data: bytes) -> np.ndarray:
    """Decodes an upload (JPEG/PNG/WEBP/HEIC), applies EXIF rotation, downscales
    the long edge to MAX_LONG_EDGE, and returns an RGB numpy array."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadTooLarge()

    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    long_edge = max(image.width, image.height)
    if long_edge > MAX_LONG_EDGE:
        scale = MAX_LONG_EDGE / long_edge
        image = image.resize(
            (round(image.width * scale), round(image.height * scale)), Image.LANCZOS
        )

    return np.array(image)


def encode_jpeg(rgb: np.ndarray) -> bytes:
    image = Image.fromarray(rgb)
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=88)
    return buf.getvalue()
