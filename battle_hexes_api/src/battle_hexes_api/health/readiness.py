"""Process-local liveness and readiness endpoints."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
def health():
    """Report process liveness without contacting AWS."""
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request):
    """Return the cached dependency state; never call AWS per request."""
    probe = getattr(request.app.state, "dynamodb_readiness_probe", None)
    if probe is not None and not probe.is_ready:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
