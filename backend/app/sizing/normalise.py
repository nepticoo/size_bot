def normalise_value(value_cm: float, criterion_kind: str, numbers_kind: str) -> float:
    """Normalises a seller's stored chart value to circumference terms.

    numbers_kind says how the seller wrote their CIRCUMFERENCE figures —
    'circumference' (full) or 'width' (flat-lay half-width, doubled here).
    A length is a length and is NEVER doubled, whatever numbers_kind says
    (scenario 18 — the single easiest thing in this codebase to get wrong).
    """
    if criterion_kind == "circumference" and numbers_kind == "width":
        return value_cm * 2
    return value_cm
