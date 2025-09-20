from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime
from decimal import Decimal


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


class PaymentResponse(BaseResponse):
    """Response model for payment operations."""
    
    payment_id: Optional[str] = None
    stripe_payment_link_id: Optional[str] = None
    payment_url: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Response model for payment status."""
    
    payment_id: str
    stripe_payment_link_id: str
    amount: Decimal
    currency: str
    status: str
    description: Optional[str] = None
    customer_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
