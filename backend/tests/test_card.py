import cv2
import numpy as np

from app.measure.card import PX_PER_MM, blur_score, find_card, is_blurry, rectify

WORLD_SCALE = 4  # px per mm in the synthetic "world" (top-down, undistorted) image


def _build_world_scene():
    """A top-down, undistorted mm-accurate scene: a card at a known spot and a
    reference rectangle of known real-world size (200mm x 100mm) elsewhere."""
    w_mm, h_mm = 600, 400
    canvas = np.full((h_mm * WORLD_SCALE, w_mm * WORLD_SCALE, 3), 235, dtype=np.uint8)

    # card: 85.6 x 53.98 mm, placed at (50,50)mm
    card_tl_mm = (50, 50)
    card_w_mm, card_h_mm = 85.60, 53.98
    card_pts_mm = np.array(
        [
            card_tl_mm,
            (card_tl_mm[0] + card_w_mm, card_tl_mm[1]),
            (card_tl_mm[0] + card_w_mm, card_tl_mm[1] + card_h_mm),
            (card_tl_mm[0], card_tl_mm[1] + card_h_mm),
        ]
    )
    card_pts_px = (card_pts_mm * WORLD_SCALE).astype(np.int32)
    cv2.fillConvexPoly(canvas, card_pts_px, (20, 20, 20))

    # reference rectangle: 200mm x 100mm, placed at (250,150)mm
    ref_tl_mm = (250, 150)
    ref_w_mm, ref_h_mm = 200.0, 100.0
    ref_pts_mm = np.array(
        [
            ref_tl_mm,
            (ref_tl_mm[0] + ref_w_mm, ref_tl_mm[1]),
            (ref_tl_mm[0] + ref_w_mm, ref_tl_mm[1] + ref_h_mm),
            (ref_tl_mm[0], ref_tl_mm[1] + ref_h_mm),
        ]
    )
    ref_pts_px = (ref_pts_mm * WORLD_SCALE).astype(np.int32)
    cv2.fillConvexPoly(canvas, ref_pts_px, (0, 140, 0))

    return canvas, ref_w_mm, ref_h_mm


def _tilt(world_img: np.ndarray) -> np.ndarray:
    """Warps the top-down world image with a perspective transform, simulating
    a hand-held phone shot at an angle."""
    h, w = world_img.shape[:2]
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
    # a modest perspective skew + rotation
    dst = np.array(
        [
            [w * 0.08, h * 0.05],
            [w * 0.95, h * 0.12],
            [w * 0.90, h * 0.93],
            [w * 0.05, h * 0.85],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(world_img, matrix, (w, h), borderValue=(235, 235, 235))


def test_card_detected_in_tilted_photo():
    world, _, _ = _build_world_scene()
    tilted = _tilt(world)
    corners = find_card(tilted)
    assert corners is not None
    assert corners.shape == (4, 2)


def test_no_card_returns_none():
    blank = np.full((400, 600, 3), 235, dtype=np.uint8)
    assert find_card(blank) is None


def test_blur_detection():
    sharp = np.zeros((200, 200), dtype=np.uint8)
    cv2.rectangle(sharp, (50, 50), (150, 150), 255, -1)
    cv2.rectangle(sharp, (60, 60), (140, 140), 0, -1)
    assert not is_blurry(sharp)

    blurry = cv2.GaussianBlur(sharp, (25, 25), 0)
    assert is_blurry(blurry)


def test_rectify_measures_known_rectangle_within_half_cm():
    world, ref_w_mm, ref_h_mm = _build_world_scene()
    tilted = _tilt(world)
    corners = find_card(tilted)
    assert corners is not None

    rectified = rectify(tilted, corners)

    # find the green reference rectangle in the rectified image and measure it
    hsv_mask = cv2.inRange(rectified, (0, 100, 0), (100, 200, 100))
    contours, _ = cv2.findContours(hsv_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    assert contours
    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    measured_w_mm = w / PX_PER_MM
    measured_h_mm = h / PX_PER_MM

    assert abs(measured_w_mm - ref_w_mm) <= 5.0  # 0.5 cm
    assert abs(measured_h_mm - ref_h_mm) <= 5.0
