from pydantic import BaseModel
from typing import Optional, Any, Dict


class BaseResponse(BaseModel):
    """Base response model."""
    ok: bool


class HealthResponse(BaseResponse):
    """Health check response."""
    pass


class CallResponse(BaseResponse):
    """Response model for call operations."""
    
    call_sid: Optional[str] = None
    to: Optional[str] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreditsResponse(BaseModel):
    email: str
    credits: int
