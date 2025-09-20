from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from ...models.requests import CallRequest
from ...models.responses import CallResponse
from ...services.call_service import CallService
from ...repositories.call_repository import CallRepository
from ...core.exceptions import BetterCallException, TwilioConfigurationError
from ..dependencies import get_call_service, get_call_repository

router = APIRouter()


@router.post("/call", response_model=CallResponse)
def make_call(
    request: CallRequest,
    call_service: CallService = Depends(get_call_service),
    call_repository: Optional[CallRepository] = Depends(get_call_repository)
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
        result = call_service.process_call_request(request, call_repository)
        
        if not result.ok:
            return JSONResponse(
                content=result.dict(),
                status_code=500
            )
        
        return result
        
    except TwilioConfigurationError as e:
        return JSONResponse(
            content={
                "ok": False,
                "error": e.message,
                "details": e.details
            },
            status_code=500
        )
    except BetterCallException as e:
        return JSONResponse(
            content={
                "ok": False,
                "error": e.message,
                "details": e.details
            },
            status_code=400
        )
    except Exception as e:
        return JSONResponse(
            content={
                "ok": False,
                "error": f"Unexpected error: {str(e)}"
            },
            status_code=500
        )
