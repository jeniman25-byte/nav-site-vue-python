from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class NavItemResponse(BaseModel):
    id: int
    title: str
    url: str
    description: str | None = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class NavCategoryResponse(BaseModel):
    id: int
    name: str
    is_private: bool
    items: list[NavItemResponse]

    model_config = ConfigDict(from_attributes=True)


class AdminCategoryCreateRequest(BaseModel):
    name: str
    is_private: bool


class AdminNavItemCreateRequest(BaseModel):
    title: str
    url: str
    description: str | None = None
    sort_order: int = 0
    category_id: int
