from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class WaitlistRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: EmailStr
    name: Optional[str] = Field(None, max_length=100)
    flag_code: Optional[str] = Field(None, max_length=64)
    notes: Optional[str] = Field(None, max_length=2000)


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: Optional[str] = None
    flag_code: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    message: str = "Waitlist signup confirmed. A confirmation email has been sent."
