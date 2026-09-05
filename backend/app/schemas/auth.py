from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class MeResponse(BaseModel):
    account_id: int
    username: str
    role: str
    shop_id: int | None = None
    shop_name: str | None = None
    acting_as_shop_id: int | None = None
    acting_as_shop_name: str | None = None
