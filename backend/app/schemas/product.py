from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    garment_type_id: int
    numbers_kind: str  # circumference | width
    shop_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    shop_url: str | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    garment_type_id: int
    numbers_kind: str
    link_code: str
    shop_url: str | None
    photo_path: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class SizeCreate(BaseModel):
    name: str


class SizeOut(BaseModel):
    id: int
    name: str
    sort_order: int
    is_complete: bool
    measurements: dict[int, float]


class MeasurementUpsert(BaseModel):
    criterion_id: int
    value_cm: float


class NumbersKindSwitch(BaseModel):
    numbers_kind: str
    confirm: bool = False
