from pydantic import BaseModel


class CriterionCreate(BaseModel):
    garment_type_id: int
    name: str
    is_main: bool = False
    kind: str  # circumference | length
    where_text: str
    measure_rule: str | None = None


class CriterionOut(BaseModel):
    id: int
    garment_type_id: int
    name: str
    is_main: bool
    kind: str
    where_text: str
    measure_rule: str | None
    sort_order: int

    model_config = {"from_attributes": True}
