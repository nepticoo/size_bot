from pydantic import BaseModel


class ShopCreate(BaseModel):
    name: str
    username: str
    instagram: str | None = None
    phone: str | None = None


class ShopOut(BaseModel):
    id: int
    name: str
    instagram: str | None
    phone: str | None
    is_active: bool
    username: str

    model_config = {"from_attributes": True}


class ShopCreateResult(BaseModel):
    shop: ShopOut
    username: str
    password: str
