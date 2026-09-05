_PERSIAN = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC = "٠١٢٣٤٥٦٧٨٩"
_LATIN = "0123456789"

_TO_LATIN = {ord(p): l for p, l in zip(_PERSIAN, _LATIN)}
_TO_LATIN.update({ord(a): l for a, l in zip(_ARABIC, _LATIN)})


def to_latin_digits(text: str) -> str:
    return text.translate(_TO_LATIN)


def parse_number(text: str) -> float:
    """Accepts Persian, Arabic-Indic or Latin digits and returns a float."""
    normalised = to_latin_digits(text).strip().replace(",", "")
    return float(normalised)
