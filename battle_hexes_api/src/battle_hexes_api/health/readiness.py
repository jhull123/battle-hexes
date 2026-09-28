"""Process-local liveness and readiness endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    """Report process liveness without contacting AWS."""
    return {"status": "ok"}


@router.get("/ready")
def ready():
    """Report readiness after FastAPI startup has completed."""
    return {"status": "ready"}
