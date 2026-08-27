from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone

class UserResponse(BaseModel):
    uid: str = Field(..., description="Supabase User UID")
    email: Optional[EmailStr] = Field(None, description="User email address")
    display_name: Optional[str] = Field(None, description="User full name")
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
