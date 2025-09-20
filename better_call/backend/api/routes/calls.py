from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from ...models.requests import CallRequest
from ...models.responses import CallResponse
from ...services.call_service import CallService
from ...repositories.call_repository import CallRepository
from ...core.exceptions import BetterCallException, TwilioConfigurationError
from ..dependencies import get_call_service, get_call_repository, get_current_user_email, get_user_repository
from ...repositories.user_repository import UserRepository
from ...core.config import settings

router = APIRouter()


@router.post("/call", response_model=CallResponse)
def make_call(
    request: CallRequest,
    call_service: CallService = Depends(get_call_service),
    call_repository: Optional[CallRepository] = Depends(get_call_repository),
    user_repo: Optional[UserRepository] = Depends(get_user_repository),
    email: Optional[str] = Depends(get_current_user_email)
):
    """
    Make a phone call with the provided parameters.
    
    Args:
        request: The call request data
        call_service: Injected call service
        call_repository: Injected call repository (optional)
        
    Returns:
        CallResponse with the result of the operation
    """
    try:
        # Enforce authentication & credits
        if user_repo is None:
            return JSONResponse(
                content={
                    "ok": False,
                    "error": "User repository unavailable",
                },
                status_code=500,
            )

        if not email:
            return JSONResponse(
                content={
                    "ok": False,
                    "error": "Unauthorized",
                    "details": {"reason": "missing_or_invalid_token"}
                },
                status_code=401,
            )

        # Attempt to consume one credit atomically
        if not user_repo.decrement_credit(email):
            return JSONResponse(
                content={
                    "ok": False,
                    "error": "Insufficient credits",
                    "details": {
                        "reason": "insufficient_credits",
                        "credits": user_repo.get_credits(email),
                        "stripe_checkout_url": settings.stripe_checkout_url or ""
                    },
                },
                status_code=402,  # Payment Required
            )

        result = call_service.process_call_request(request, call_repository)
        
        if not result.ok:
            # Compensate: refund the consumed credit
            try:
                user_repo.increment_credit(email, 1)
            except Exception:
                pass
            return JSONResponse(
                content=result.dict(),
                status_code=500
            )
        
        return result
        
    except TwilioConfigurationError as e:
        # Compensate on configuration failure as well
        try:
            if email and user_repo:
                user_repo.increment_credit(email, 1)
        except Exception:
            pass
        return JSONResponse(
            content={
                "ok": False,
                "error": e.message,
                "details": e.details
            },
            status_code=500
        )
    except BetterCallException as e:
        try:
            if email and user_repo:
                user_repo.increment_credit(email, 1)
        except Exception:
            pass
        return JSONResponse(
            content={
                "ok": False,
                "error": e.message,
                "details": e.details
            },
            status_code=400
        )
    except Exception as e:
        try:
            if email and user_repo:
                user_repo.increment_credit(email, 1)
        except Exception:
            pass
        return JSONResponse(
            content={
                "ok": False,
                "error": f"Unexpected error: {str(e)}"
            },
            status_code=500
        )
