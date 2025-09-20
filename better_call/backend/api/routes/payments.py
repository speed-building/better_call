from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional
import json

from ...models.requests import PaymentRequest
from ...models.responses import PaymentResponse, PaymentStatusResponse
from ...services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create", response_model=PaymentResponse)
async def create_payment(payment_request: PaymentRequest):
    payment_service = PaymentService()
    
    try:
        result = await payment_service.create_payment_link(
            amount=payment_request.amount,
            currency=payment_request.currency,
            success_url=payment_request.success_url,
            cancel_url=payment_request.cancel_url,
            description=payment_request.description,
            customer_email=payment_request.customer_email
        )
        
        if not result.ok:
            raise HTTPException(status_code=400, detail=result.error)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    payment_service = PaymentService()
    
    try:
        payload = await request.body()
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        if not payment_service.verify_webhook_signature(payload, stripe_signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        try:
            event = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        event_type = event.get('type')
        
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            
            payment_link_id = session.get('payment_link')
            
            if payment_link_id:
                success = await payment_service.handle_payment_success(payment_link_id)
                if not success:
                    print(f"Failed to process payment success for {payment_link_id}")
            else:
                print("No payment link ID found in checkout session")
        
        else:
            print(f"Unhandled webhook event type: {event_type}")
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
