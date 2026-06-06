"""Health check routes."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Return service health status."""
    db = request.app.state.db
    return {
        "status": "ok",
        "service": "nexuschat",
        "database": db.db_type,
    }
