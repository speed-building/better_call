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
    
    amount: Decimal = Field(gt=0, description="Payment amount")
    currency: str = Field(default="usd", description="Payment currency")
    description: Optional[str] = Field(default="", description="Payment description")
    customer_email: Optional[str] = Field(default=None, description="Customer email")
    success_url: str = Field(description="URL to redirect after successful payment")
    cancel_url: str = Field(description="URL to redirect after cancelled payment")
