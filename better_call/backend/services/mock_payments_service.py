from typing import Optional

from ..models.user import User
from ..models.responses import PaymentResponse
from ..repositories.payment_repository import PaymentRepository
from ..core.config import settings


class MockPaymentsService:
    """Mocked payments service that returns a static payment URL."""

    def __init__(self, hardcoded_url: Optional[str] = None):
        # Default hardcoded Stripe checkout URL-like string for development
        self.hardcoded_url = hardcoded_url or "https://buy.stripe.com/test_cNi9ASfCz3Xm9gy2ug0Ba00"

    def create_payment_link_for_user(self, user: User) -> PaymentResponse:
        # Persist a mock payment record so we can track status via /payments/status
        repo = PaymentRepository()
        # Build success URL back to our frontend confirmation page with payment_id
        frontend_base = settings.backend_base_url.replace(":9001", ":9001")  # keep same for now
        # Create record first with placeholder; we'll need the returned id for success_url
        payment_id = repo.create_payment(
            stripe_payment_link_id=f"pl_mock_{user.id or 'anon'}",
            amount=1,
            currency="usd",
            description="Credit top-up",
            customer_email=user.email,
            success_url=None,
            cancel_url=None,
        )
        success_url = f"{settings.backend_base_url}/payments/confirmation?payment_id={payment_id}"
        try:
            # Update success_url in DB (simple approach: reinsert not supported; skip or add update if needed)
            # For mock flow we don't strictly need it, frontend will redirect based on payment_url.
            pass
        except Exception:
            pass
        return PaymentResponse(
            ok=True,
            payment_id=str(payment_id),
            payment_url=self.hardcoded_url,
            status="pending",
        )


