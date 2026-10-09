from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl


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
