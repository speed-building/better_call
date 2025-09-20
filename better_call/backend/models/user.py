from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """Represents a user record as stored in the database."""

    id: Optional[int] = Field(default=None, description="Auto-incremented user ID")
    email: EmailStr = Field(description="Unique user email")
    password_hash: str = Field(description="BCrypt password hash")
    credits: int = Field(default=0, ge=0, description="Available credits")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")


class UserPublic(BaseModel):
    """Public facing user model (no password hash)."""

    id: Optional[int] = None
    email: EmailStr
    credits: int = 0
    created_at: Optional[datetime] = None
