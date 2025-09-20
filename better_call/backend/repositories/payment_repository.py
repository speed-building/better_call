from typing import Optional, Dict, Any
from decimal import Decimal

from ...database.db import PromptDB
from ..core.config import settings


class PaymentRepository:
    """Repository for payment data operations."""
    
    def __init__(self):
        self.db = PromptDB(settings.db_path)
    
    def create_payment(self, stripe_payment_link_id: str, amount: Decimal, currency: str = "usd", 
                      description: Optional[str] = None, customer_email: Optional[str] = None,
                      success_url: Optional[str] = None, cancel_url: Optional[str] = None) -> int:
        """Create a new payment record."""
        return self.db.insert_payment(
            stripe_payment_link_id=stripe_payment_link_id,
            amount=amount,
            currency=currency,
            description=description,
            customer_email=customer_email,
            success_url=success_url,
            cancel_url=cancel_url
        )
    
    def update_payment_status(self, stripe_payment_link_id: str, status: str) -> bool:
        """Update payment status."""
        return self.db.update_payment_status(stripe_payment_link_id, status)
    
    def get_payment_by_stripe_id(self, stripe_payment_link_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by Stripe payment link ID."""
        return self.db.get_payment_by_stripe_id(stripe_payment_link_id)
    
    def get_payment_by_id(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Get payment by internal payment ID."""
        return self.db.get_payment_by_id(payment_id)
