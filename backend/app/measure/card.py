import cv2
import numpy as np

# ISO/IEC 7810 ID-1 (national ID, metro card, bank card): 85.60 x 53.98 mm.
CARD_WIDTH_MM = 85.60
CARD_HEIGHT_MM = 53.98
CARD_RATIO = CARD_WIDTH_MM / CARD_HEIGHT_MM  # 1.5858

PX_PER_MM = 10
BLUR_THRESHOLD = 60.0


def blur_score(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(gray: np.ndarray, threshold: float = BLUR_THRESHOLD) -> bool:
    return blur_score(gray) < threshold


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Orders 4 points as top-left, top-right, bottom-right, bottom-left."""
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).flatten()
    top_left = pts[np.argmin(s)]
    bottom_right = pts[np.argmax(s)]
    top_right = pts[np.argmin(diff)]
    bottom_left = pts[np.argmax(diff)]
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def find_card(bgr: np.ndarray) -> np.ndarray | None:
    """Finds the best bank-card-shaped quadrilateral in the frame.
    Returns ordered 4 corners (float32) or None."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 40, 120)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    frame_area = bgr.shape[0] * bgr.shape[1]

    best = None
    best_score = -1.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < frame_area * 0.002 or area > frame_area * 0.15:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue

        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = area / hull_area
        if solidity < 0.9:
            continue

        pts = _order_corners(approx.reshape(4, 2).astype(np.float32))
        width = (np.linalg.norm(pts[1] - pts[0]) + np.linalg.norm(pts[2] - pts[3])) / 2
        height = (np.linalg.norm(pts[3] - pts[0]) + np.linalg.norm(pts[2] - pts[1])) / 2
        if height == 0:
            continue
        ratio = max(width, height) / min(width, height)
        ratio_error = abs(ratio - CARD_RATIO)
        if ratio_error > 0.25:
            continue

        score = solidity - ratio_error
        if score > best_score:
            best_score = score
            best = pts

    return best


MAX_CANVAS_EDGE = 9000


def rectify(bgr: np.ndarray, card_corners: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Warps the frame so the card plane is exactly PX_PER_MM px/mm and level.
    Returns (warped_image, card_rect) where card_rect = (x, y, w, h) of the
    card's own position in the output, so callers can exclude it from segmentation."""
    dst_w = CARD_WIDTH_MM * PX_PER_MM
    dst_h = CARD_HEIGHT_MM * PX_PER_MM

    # decide orientation: if the detected card is taller than wide in the image,
    # map it to a portrait destination card of the same physical proportions.
    src = card_corners
    width = (np.linalg.norm(src[1] - src[0]) + np.linalg.norm(src[2] - src[3])) / 2
    height = (np.linalg.norm(src[3] - src[0]) + np.linalg.norm(src[2] - src[1])) / 2
    if width < height:
        dst_w, dst_h = dst_h, dst_w

    dst_at_origin = np.array(
        [[0, 0], [dst_w, 0], [dst_w, dst_h], [0, dst_h]], dtype=np.float32
    )
    matrix = cv2.getPerspectiveTransform(src, dst_at_origin)

    # find how much of the plane the whole original frame covers once rectified,
    # so the canvas is sized to hold all of it rather than an arbitrary guess
    h, w = bgr.shape[:2]
    frame_corners = np.array([[[0, 0]], [[w, 0]], [[w, h]], [[0, h]]], dtype=np.float32)
    warped_corners = cv2.perspectiveTransform(frame_corners, matrix).reshape(-1, 2)
    min_xy = warped_corners.min(axis=0)
    max_xy = warped_corners.max(axis=0)

    out_w = int(np.clip(max_xy[0] - min_xy[0], dst_w, MAX_CANVAS_EDGE))
    out_h = int(np.clip(max_xy[1] - min_xy[1], dst_h, MAX_CANVAS_EDGE))

    shift = np.array([[1, 0, -min_xy[0]], [0, 1, -min_xy[1]], [0, 0, 1]], dtype=np.float32)
    matrix = shift @ matrix

    # BORDER_REPLICATE avoids a black void in the corners the bounding-box
    # canvas adds beyond the actual rotated frame (which would otherwise be
    # mistaken for content when segmenting); it extends the nearest real
    # edge pixels instead, which is background almost everywhere that matters.
    warped = cv2.warpPerspective(
        bgr, matrix, (out_w, out_h), borderMode=cv2.BORDER_REPLICATE
    )
    card_rect = (int(-min_xy[0]), int(-min_xy[1]), int(dst_w), int(dst_h))
    return warped, card_rect
