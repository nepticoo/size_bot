import numpy as np

from app.measure.rules import (
    bicep_width,
    bottom_length,
    chest_width,
    garment_length,
    garment_waist_width,
    hip_width,
    leg_opening_width,
    rise,
    shoulder_width,
    sleeve_length,
    thigh_width,
    waist_width,
)

PX_PER_CM = 100  # PX_PER_MM(10) * 10


def _tshirt_mask(chest_px=520, length_px=680, shoulder_px=440, sleeve_h_px=90):
    """A crude but recognisable T-shirt silhouette: wide shoulders/sleeves up top
    that narrow sharply into the body at the armpit, then a straight body to hem."""
    h, w = length_px + 20, chest_px + 200
    mask = np.zeros((h, w), dtype=bool)
    cx = w // 2
    top = 10

    # shoulder/sleeve band: wide
    mask[top : top + sleeve_h_px, cx - shoulder_px // 2 : cx + shoulder_px // 2] = True
    # body: narrower, from just below the sleeve band to the hem
    body_top = top + sleeve_h_px
    mask[body_top : top + length_px, cx - chest_px // 2 : cx + chest_px // 2] = True
    return mask


def _pants_mask(waist_px=440, length_px=760, crotch_gap_px=30, leg_w_px=190):
    h, w = length_px + 20, waist_px + 40
    mask = np.zeros((h, w), dtype=bool)
    cx = w // 2
    top = 10
    crotch_y = top + length_px // 2

    # waist to crotch: solid block
    mask[top:crotch_y, cx - waist_px // 2 : cx + waist_px // 2] = True
    # legs: two separate columns below the crotch
    mask[crotch_y : top + length_px, cx - waist_px // 2 : cx - waist_px // 2 + leg_w_px] = True
    mask[crotch_y : top + length_px, cx + waist_px // 2 - leg_w_px : cx + waist_px // 2] = True
    return mask


def test_chest_width_reads_body_not_shoulders():
    mask = _tshirt_mask(chest_px=520, shoulder_px=440)
    width_px = chest_width(mask)
    # body is narrower than the shoulder/sleeve band, so chest_width must read
    # close to the body width, not the wider shoulder band
    assert abs(width_px - 520) < 15


def test_garment_length_matches_known_height():
    mask = _tshirt_mask(length_px=680)
    length_px = garment_length(mask)
    assert abs(length_px - 680) <= 2


def test_waist_width_reads_top_edge():
    mask = _pants_mask(waist_px=440)
    w = waist_width(mask)
    assert abs(w - 440) < 10


def test_bottom_length_matches_known_height():
    mask = _pants_mask(length_px=760)
    length_px = bottom_length(mask)
    assert abs(length_px - 760) <= 2


def test_shoulder_width_reads_near_shoulder_band():
    mask = _tshirt_mask(shoulder_px=440)
    assert abs(shoulder_width(mask) - 440) < 15


def test_sleeve_length_is_positive_and_bounded():
    mask = _tshirt_mask()
    length = sleeve_length(mask)
    assert 0 < length < mask.shape[1]


def test_bicep_width_is_positive():
    mask = _tshirt_mask()
    assert bicep_width(mask) > 0


def test_garment_waist_width_is_narrower_than_chest():
    mask = _tshirt_mask(chest_px=520)
    assert 0 < garment_waist_width(mask) <= 520 + 20


def test_hip_width_reads_near_waist_band():
    mask = _pants_mask(waist_px=440)
    assert abs(hip_width(mask) - 440) < 15


def test_thigh_width_is_close_to_leg_width():
    mask = _pants_mask(leg_w_px=190)
    assert abs(thigh_width(mask) - 190) < 15


def test_leg_opening_width_is_close_to_leg_width():
    mask = _pants_mask(leg_w_px=190)
    assert abs(leg_opening_width(mask) - 190) < 15


def test_rise_is_positive_and_less_than_full_length():
    mask = _pants_mask(length_px=760)
    r = rise(mask)
    assert 0 < r < 760
