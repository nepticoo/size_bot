import json

from app.sizing.compare import CriterionInfo, SizeChart, compute_answer, fit_word
from app.sizing.normalise import normalise_value

CHEST = CriterionInfo(id=1, name="دورِ سینه", kind="circumference", is_main=True)
LENGTH = CriterionInfo(id=2, name="طولِ لباس", kind="length", is_main=True)
SHOULDER = CriterionInfo(id=3, name="عرضِ شانه", kind="length", is_main=False)
SLEEVE = CriterionInfo(id=4, name="طولِ آستین", kind="length", is_main=False)
CRITERIA = [CHEST, LENGTH, SHOULDER, SLEEVE]


def _product_a_sizes():
    # test-scenarios.md sample data, product A, numbers_kind = circumference
    return [
        SizeChart(id=1, name="اسمال", values={1: 96, 2: 66, 3: 42, 4: 20}),
        SizeChart(id=2, name="مدیوم", values={1: 104, 2: 68, 3: 44, 4: 21}),
        SizeChart(id=3, name="لارج", values={1: 112, 2: 70, 3: 46, 4: 22}),
        SizeChart(id=4, name="ایکس‌لارج", values={1: 120, 2: 72, 3: 48, 4: 23}),
    ]


# ---- E1: normalise -----------------------------------------------------


def test_circumference_doubled_when_seller_used_width():
    assert normalise_value(52, "circumference", "width") == 104


def test_circumference_unchanged_when_seller_used_circumference():
    assert normalise_value(104, "circumference", "circumference") == 104


def test_length_never_doubled_scenario_18():
    # the whole point of scenario 18: a length must never be doubled,
    # whatever numbers_kind says
    assert normalise_value(68, "length", "width") == 68
    assert normalise_value(68, "length", "circumference") == 68


def test_product_entered_as_width_answers_identically_scenario_18():
    sizes_circ = _product_a_sizes()
    sizes_width_raw = [
        SizeChart(id=1, name="اسمال", values={1: 48, 2: 66, 3: 21, 4: 10}),
        SizeChart(id=2, name="مدیوم", values={1: 52, 2: 68, 3: 22, 4: 10.5}),
        SizeChart(id=3, name="لارج", values={1: 56, 2: 70, 3: 23, 4: 11}),
        SizeChart(id=4, name="ایکس‌لارج", values={1: 60, 2: 72, 3: 24, 4: 11.5}),
    ]
    sizes_width_normalised = [
        SizeChart(
            id=s.id,
            name=s.name,
            values={cid: normalise_value(v, next(c.kind for c in CRITERIA if c.id == cid), "width") for cid, v in s.values.items()},
        )
        for s in sizes_width_raw
    ]

    buyer = {1: 104, 2: 68}  # tshirt-1: chest span doubled to 104 by the pipeline, length 68
    r1 = compute_answer(buyer, sizes_circ, CRITERIA)
    r2 = compute_answer(buyer, sizes_width_normalised, CRITERIA)
    assert r1["status"] == r2["status"] == "answered"
    assert r1["recommended_size"]["name"] == r2["recommended_size"]["name"] == "مدیوم"


# ---- E2/E3: fit bands, recommendation, no-fit --------------------------


def test_fit_band_boundaries():
    assert fit_word(-10) == "خیلی تنگ‌تر از لباسِ خودت"
    assert fit_word(-6.1) == "خیلی تنگ‌تر از لباسِ خودت"
    assert fit_word(-4) == "تنگ‌تر از لباسِ خودت"
    assert fit_word(0) == "مثلِ لباسِ خودت"
    assert fit_word(3) == "مثلِ لباسِ خودت"
    assert fit_word(5) == "کمی آزادتر"
    assert fit_word(8) == "کمی آزادتر"
    assert fit_word(9) == "آزاد"


def test_scenario_1_tshirt1_recommends_medium():
    buyer = {1: 104, 2: 68}
    result = compute_answer(buyer, _product_a_sizes(), CRITERIA)
    assert result["status"] == "answered"
    assert result["recommended_size"]["name"] == "مدیوم"
    fit_by_name = {s["name"]: s["fit_word"] for s in result["sizes"]}
    # per decision 53's exact bands (chest diff -8cm falls below the -6 cutoff)
    assert fit_by_name["اسمال"] == "خیلی تنگ‌تر از لباسِ خودت"
    assert fit_by_name["مدیوم"] == "مثلِ لباسِ خودت"
    assert fit_by_name["لارج"] == "کمی آزادتر"
    assert fit_by_name["ایکس‌لارج"] == "آزاد"


def test_scenario_4_tshirt2_recommends_large_with_length_note():
    buyer = {1: 112, 2: 68}  # chest doubled to 112 (large), garment length differs from 70
    result = compute_answer(buyer, _product_a_sizes(), CRITERIA)
    assert result["status"] == "answered"
    assert result["recommended_size"]["name"] == "لارج"
    assert result["length_note"] is not None


def test_scenario_5_tshirt3_no_size_fits():
    buyer = {1: 140, 2: 80}  # chest doubled to 140, far beyond XL(120)
    result = compute_answer(buyer, _product_a_sizes(), CRITERIA)
    assert result["status"] == "no_fit"
    assert result["nearest_size"]["name"] == "ایکس‌لارج"


def test_no_raw_measurement_anywhere_in_answer_scenario_1_e5():
    buyer = {1: 104, 2: 68}
    result = compute_answer(buyer, _product_a_sizes(), CRITERIA)
    serialised = json.dumps(result, ensure_ascii=False)
    # none of the actual cm figures used anywhere in this test's data should
    # leak into the answer payload
    for forbidden in ["96", "104", "112", "120", "66", "68", "70", "72"]:
        assert forbidden not in serialised
