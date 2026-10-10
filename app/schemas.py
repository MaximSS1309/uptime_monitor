from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class SiteCreate(BaseModel):
    name: str
    url: HttpUrl


class SiteUpdate(BaseModel):
    name: str | None = None
    url: HttpUrl | None = None



class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    status_code: int | None
    is_online: bool


class CheckLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: int
    status_code: int
    is_online: bool
    checked_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str
