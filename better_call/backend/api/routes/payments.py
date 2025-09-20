from fastapi import APIRouter, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import json

from ...models.responses import PaymentResponse
from ...models.user import User
from ...services.payment_service import PaymentService
from ...repositories.user_repository import UserRepository
from ..dependencies import get_user_repository, get_current_user_email

router = APIRouter(prefix="/payments", tags=["payments"])


def get_current_user(
    user_repo: UserRepository = Depends(get_user_repository),
    email: Optional[str] = Depends(get_current_user_email)
) -> User:
    """Get the current authenticated user."""
    if not user_repo:
        raise HTTPException(status_code=500, detail="User repository unavailable")
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user_dict = user_repo.get_user_by_email(email)
    if not user_dict:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_dict)


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    current_user: User = Depends(get_current_user)
):
    payment_service = PaymentService()
    
    try:
        result = await payment_service.create_payment_link(
            user=current_user
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


@router.get("/status")
async def get_payment_status(payment_id: str | None = None, stripe_payment_link_id: str | None = None):
    payment_service = PaymentService()
    try:
        result = await payment_service.get_payment_status(
            payment_id=payment_id,
            stripe_payment_link_id=stripe_payment_link_id,
        )
        if not result:
            return JSONResponse(content={"exists": False}, status_code=404)
        return JSONResponse(content={"exists": True, "status": result.status, "data": result.dict()}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")
