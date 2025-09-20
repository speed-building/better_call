from fastapi import APIRouter
from .health import router as health_router
from .calls import router as calls_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(calls_router, prefix="/api", tags=["calls"])
