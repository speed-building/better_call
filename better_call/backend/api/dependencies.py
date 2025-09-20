from fastapi import Depends, Request, Header
from typing import Optional

from ..repositories.call_repository import CallRepository
from ..repositories.user_repository import UserRepository
from ..services.call_service import CallService
from ..core.config import settings
from ..core.security import decode_access_token


def get_call_repository(request: Request) -> Optional[CallRepository]:
    """Dependency to get the call repository from app state."""
    return getattr(request.app.state, 'call_repository', None)


def get_call_service() -> CallService:
    """Dependency to get the call service."""
    return CallService()


def get_user_repository(request: Request) -> Optional[UserRepository]:
    """Dependency to get the user repository from app state."""
    return getattr(request.app.state, 'user_repository', None)


def get_current_user_email(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    return payload.get("sub") if payload else None
