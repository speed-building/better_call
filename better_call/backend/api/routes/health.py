from fastapi import APIRouter

from ...models.responses import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(ok=True)
