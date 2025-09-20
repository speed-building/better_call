from pydantic import BaseModel, Field
from typing import Optional


class CallRequest(BaseModel):
    """Request model for making a call."""
    
    name: str = Field(min_length=1, description="Name of the person making the request")
    email: str = Field(description="Email address of the requester")
    destination: str = Field(
        pattern=r"^\+\d{8,15}$", 
        description="Destination phone number in international format"
    )
    prompt: Optional[str] = Field(
        default="", 
        description="Optional prompt to customize the call behavior"
    )


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str
