from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from ...models.requests import CallRequest
from ...models.responses import CallResponse, PaymentResponse
from ...services.call_service import CallService
from ...repositories.call_repository import CallRepository
from ...core.exceptions import BetterCallException, TwilioConfigurationError
from ..dependencies import (
    get_call_service,
    get_call_repository,
    get_current_user_email,
    get_user_repository,
    get_payments_service,
)
from ...services.mock_payments_service import MockPaymentsService
from ...repositories.user_repository import UserRepository
from ...core.config import settings

router = APIRouter()


@router.post("/call", response_model=CallResponse)
def make_call(
    request: CallRequest,
    call_service: CallService = Depends(get_call_service),
    call_repository: Optional[CallRepository] = Depends(get_call_repository),
    user_repo: Optional[UserRepository] = Depends(get_user_repository),
    email: Optional[str] = Depends(get_current_user_email),
    payments_service: MockPaymentsService = Depends(get_payments_service),
):
    """Make a phone call with the provided parameters."""
    try:
        # Enforce authentication & credits
        if user_repo is None:
            return JSONResponse(content={"ok": False, "error": "User repository unavailable"}, status_code=500)

        if not email:
            return JSONResponse(
                content={"ok": False, "error": "Unauthorized", "details": {"reason": "missing_or_invalid_token"}},
                status_code=401,
            )

        # Attempt to consume one credit atomically
        if not user_repo.decrement_credit(email):
            # Use mocked payments service to generate a payment link for the user
            from ...models import User

            user = user_repo.get_user_by_email(email)
            user_model = User(
                id=user.get("id") if user else None,
                email=email,
                password_hash=user.get("password_hash") if user else "",
                credits=user.get("credits") if user else 0,
                created_at=None,
            )

            # Save the call request so we can trigger it after payment
            try:
                if call_repository is not None:
                    call_repository.insert_call_request(
                        email=request.email,
                        phone_to=request.destination,
                        prompt=request.prompt or "",
                    )
            except Exception:
                pass

            payment_resp: PaymentResponse = payments_service.create_payment_link_for_user(user_model)
            return JSONResponse(
                content={
                    "ok": False,
                    "error": "Insufficient credits",
                    "details": {
                        "reason": "insufficient_credits",
                        "credits": user_repo.get_credits(email),
                        "payment_url": payment_resp.payment_url,
                        "payment_id": payment_resp.payment_id,
                    },
                },
                status_code=402,
            )

        # Proceed with the call using available credits
        result = call_service.process_call_request(request, call_repository)
        if not result.ok:
            try:
                user_repo.increment_credit(email, 1)
            except Exception:
                pass
            return JSONResponse(content=result.dict(), status_code=500)
        return result

    except TwilioConfigurationError as e:
        try:
            if email and user_repo:
                user_repo.increment_credit(email, 1)
        except Exception:
            pass
        return JSONResponse(content={"ok": False, "error": e.message, "details": e.details}, status_code=500)
    except BetterCallException as e:
        try:
            if email and user_repo:
                user_repo.increment_credit(email, 1)
        except Exception:
            pass
        return JSONResponse(content={"ok": False, "error": e.message, "details": e.details}, status_code=400)
    except Exception as e:
        try:
            if email and user_repo:
                user_repo.increment_credit(email, 1)
        except Exception:
            pass
        return JSONResponse(content={"ok": False, "error": f"Unexpected error: {str(e)}"}, status_code=500)


@router.get("/call/last")
def get_last_call_request(
    call_repository: Optional[CallRepository] = Depends(get_call_repository),
    email: Optional[str] = Depends(get_current_user_email),
):
    if not email:
        return JSONResponse(
            content={"error": "Unauthorized"},
            status_code=401,
        )
    if call_repository is None:
        return JSONResponse(
            content={"error": "Repository unavailable"},
            status_code=500,
        )
    try:
        record = call_repository.get_last_call_request_by_email(email)
        return JSONResponse(content={"record": record}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
