import cv2
import numpy as np

BORDER_TOUCH_LIMIT = 0.02  # garment_cropped if the mask touches the frame edge
# on more than this fraction of its perimeter
LAB_DISTANCE_THRESHOLD = 22.0


class GarmentCropped(Exception):
    pass


def _sample_background_lab(lab: np.ndarray, corner_size: int = 30) -> np.ndarray:
    """Samples background colour from the four corners of the frame, per
    architecture.md — the card sits ON the garment, so corners (not the
    card's surroundings) are where clear table background is guaranteed."""
    h, w = lab.shape[:2]
    s = min(corner_size, h // 4, w // 4) or 1
    samples = np.concatenate(
        [
            lab[0:s, 0:s].reshape(-1, 3),
            lab[0:s, w - s : w].reshape(-1, 3),
            lab[h - s : h, 0:s].reshape(-1, 3),
            lab[h - s : h, w - s : w].reshape(-1, 3),
        ]
    )
    return samples.mean(axis=0)


def segment_garment(
    bgr: np.ndarray, card_rect: tuple[int, int, int, int]
) -> np.ndarray:
    """Returns a boolean mask of the garment silhouette, excluding the card.
    Raises GarmentCropped if the garment mask runs off the frame."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    bg = _sample_background_lab(lab)

    dist = np.linalg.norm(lab - bg, axis=2)
    fg = dist > LAB_DISTANCE_THRESHOLD

    fg_u8 = (fg.astype(np.uint8)) * 255
    kernel = np.ones((9, 9), np.uint8)
    closed = cv2.morphologyEx(fg_u8, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    if num_labels <= 1:
        raise GarmentCropped()

    largest_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mask = labels == largest_label

    # fill holes
    filled = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
    mask = filled > 0

    # exclude the card itself only after hole-filling, so the card-shaped gap
    # it left in the garment silhouette is not treated as a hole to patch over
    cx, cy, cw, ch = card_rect
    mask[max(cy, 0) : cy + ch, max(cx, 0) : cx + cw] = False

    _check_not_cropped(mask)
    return mask


def _check_not_cropped(mask: np.ndarray) -> None:
    h, w = mask.shape
    border_pixels = np.count_nonzero(mask[0, :]) + np.count_nonzero(mask[-1, :])
    border_pixels += np.count_nonzero(mask[:, 0]) + np.count_nonzero(mask[:, -1])
    perimeter = 2 * (h + w)
    if perimeter > 0 and border_pixels / perimeter > BORDER_TOUCH_LIMIT:
        raise GarmentCropped()
