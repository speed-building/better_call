from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


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

class PaymentRequest(BaseModel):
    """Request model for creating a payment."""
    
    # Todos os parâmetros agora vêm das configurações do .env
    # Este modelo pode ser usado para futuras extensões se necessário
    pass

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str
