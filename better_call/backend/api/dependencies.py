from fastapi import Depends, Request
from typing import Optional

from ..repositories.call_repository import CallRepository
from ..services.call_service import CallService
from ..core.config import settings


def get_call_repository(request: Request) -> Optional[CallRepository]:
    """Dependency to get the call repository from app state."""
    return getattr(request.app.state, 'call_repository', None)


def get_call_service() -> CallService:
    """Dependency to get the call service."""
    return CallService()
