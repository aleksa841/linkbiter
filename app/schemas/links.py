from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkCreateResponse(BaseModel):
    url: HttpUrl
    short_code: str
    short_url: str
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    new_short_code: str

class LinkStats(BaseModel):
    url: HttpUrl
    created_at: datetime
    clicks: int
    last_used_at: Optional[datetime] = None