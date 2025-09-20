from fastapi import APIRouter
from .health import router as health_router
from .calls import router as calls_router
from .payments import router as payments_router
from .auth import router as auth_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(calls_router, prefix="/api", tags=["calls"])
router.include_router(payments_router, prefix="/api", tags=["payments"])
router.include_router(auth_router)
