import stripe
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from ..core.config import settings
from ..models.responses import PaymentResponse, PaymentStatusResponse
from ..repositories.payment_repository import PaymentRepository


class PaymentService:
    """Service for handling Stripe payments."""
    
    def __init__(self):
        stripe.api_key = settings.stripe_secret_key
        self.payment_repo = PaymentRepository()
    
    async def create_payment_link(
        self, 
        amount: Decimal, 
        currency: str, 
        success_url: str, 
        cancel_url: str,
        description: Optional[str] = None, 
        customer_email: Optional[str] = None
    ) -> PaymentResponse:
        try:
            amount_cents = int(amount * 100)
            
            payment_id = self.payment_repo.create_payment(
                stripe_payment_link_id=None,
                amount=amount,
                currency=currency,
                description=description,
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            # Construir URLs com o payment_id
            success_url_with_id = f"{success_url}?payment_id={payment_id}"
            cancel_url_with_id = f"{cancel_url}?payment_id={payment_id}"
            
            # Criar o payment link no Stripe com as URLs que incluem o payment_id
            payment_link = stripe.PaymentLink.create(
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': description or 'Payment',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                after_completion={
                    'type': 'redirect',
                    'redirect': {'url': success_url_with_id}
                },
                automatic_tax={'enabled': False},
                billing_address_collection='auto',
                shipping_address_collection=None,
                phone_number_collection={'enabled': False},
                custom_fields=[],
                custom_text={},
                invoice_creation={'enabled': False},
                payment_method_types=['card'],
                submit_type='pay',
                metadata={
                    'customer_email': customer_email or '',
                    'description': description or '',
                    'payment_id': str(payment_id),
                }
            )
            
            # Atualizar o payment com o stripe_payment_link_id
            self.payment_repo.update_payment_stripe_id(payment_id, payment_link.id)
            
            return PaymentResponse(
                ok=True,
                payment_id=str(payment_id),
                stripe_payment_link_id=payment_link.id,
                payment_url=payment_link.url,
                amount=amount,
                currency=currency,
                status='pending'
            )
            
        except stripe.error.StripeError as e:
            return PaymentResponse(
                ok=False,
                error=f"Stripe error: {str(e)}"
            )
        except Exception as e:
            return PaymentResponse(
                ok=False,
                error=f"Payment creation failed: {str(e)}"
            )
    
    async def handle_payment_success(self, stripe_payment_link_id: str) -> bool:
        try:
            success = self.payment_repo.update_payment_status(stripe_payment_link_id, 'paid')
            
            if success:
                print(f"Payment {stripe_payment_link_id} marked as paid successfully")
                return True
            else:
                print(f"Failed to update payment status for {stripe_payment_link_id}")
                return False
                
        except Exception as e:
            print(f"Error handling payment success for {stripe_payment_link_id}: {str(e)}")
            return False
    
    async def get_payment_status(self, payment_id: Optional[str] = None, 
                               stripe_payment_link_id: Optional[str] = None) -> Optional[PaymentStatusResponse]:
        try:
            payment_data = None
            
            if payment_id:
                payment_data = self.payment_repo.get_payment_by_id(int(payment_id))
            elif stripe_payment_link_id:
                payment_data = self.payment_repo.get_payment_by_stripe_id(stripe_payment_link_id)
            
            if not payment_data:
                return None
            
            return PaymentStatusResponse(
                payment_id=str(payment_data['id']),
                stripe_payment_link_id=payment_data['stripe_payment_link_id'],
                amount=Decimal(str(payment_data['amount'])),
                currency=payment_data['currency'],
                status=payment_data['status'],
                description=payment_data['description'],
                customer_email=payment_data['customer_email'],
                created_at=datetime.fromisoformat(payment_data['created_at']),
                updated_at=datetime.fromisoformat(payment_data['updated_at'])
            )
            
        except Exception as e:
            print(f"Error getting payment status: {str(e)}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        try:
            stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            return False
