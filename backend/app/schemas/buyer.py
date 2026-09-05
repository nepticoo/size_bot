from pydantic import BaseModel


class ProductPublicOut(BaseModel):
    shop_name: str
    product_name: str
    photo_url: str | None
    is_active: bool


class MeasureResult(BaseModel):
    status: str  # rejected | answered
    reason: str | None = None
    view_code: str | None = None


class SizeAnswerOut(BaseModel):
    id: int
    name: str
    fit_word: str
    is_recommended: bool


class AnswerOut(BaseModel):
    status: str  # answered | no_fit
    shop_name: str
    product_name: str
    shop_url: str | None
    recommended_size: dict | None = None
    nearest_size: dict | None = None
    sizes: list[dict]
    length_note: str | None = None
    secondary_notes: list[str] = []
