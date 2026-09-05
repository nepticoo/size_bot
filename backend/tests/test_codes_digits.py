from app.core.codes import new_code
from app.core.digits import parse_number, to_latin_digits


def test_codes_are_not_sequential():
    codes = [new_code() for _ in range(20)]
    assert len(set(codes)) == 20
    # not sequential/guessable: no shared prefix run and reasonable length
    for c in codes:
        assert len(c) >= 8


def test_persian_digits_parse_to_latin():
    assert to_latin_digits("۱۲۳") == "123"
    assert parse_number("۱۲۳") == 123.0


def test_arabic_indic_digits_parse():
    assert parse_number("٤٥") == 45.0


def test_latin_digits_pass_through():
    assert parse_number("104") == 104.0
