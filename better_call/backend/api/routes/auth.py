from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional

from ...models.requests import RegisterRequest, LoginRequest
from ...models.responses import TokenResponse, CreditsResponse
from ...repositories.user_repository import UserRepository
from ...core.security import create_access_token, decode_access_token
from ..dependencies import get_user_repository


router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user_email(
    authorization: Optional[str] = Header(default=None)
) -> Optional[str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    return payload.get("sub") if payload else None


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, user_repo: UserRepository = Depends(get_user_repository)):
    if user_repo is None:
        raise HTTPException(status_code=500, detail="User repository unavailable")
    try:
        # Always create with zero credits; ignore any client-supplied credits
        user_repo.create_user(request.email, request.password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = create_access_token(request.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, user_repo: UserRepository = Depends(get_user_repository)):
    if user_repo is None:
        raise HTTPException(status_code=500, detail="User repository unavailable")
    if not user_repo.verify_user(request.email, request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(request.email)
    return TokenResponse(access_token=token)


@router.get("/credits", response_model=CreditsResponse)
def get_credits(
    user_repo: UserRepository = Depends(get_user_repository),
    email: Optional[str] = Depends(get_current_user_email),
):
    if user_repo is None:
        raise HTTPException(status_code=500, detail="User repository unavailable")
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return CreditsResponse(email=email, credits=user_repo.get_credits(email))


