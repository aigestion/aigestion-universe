"""Health check routes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    uptime_seconds: float

@router.get("/health", response_model=HealthResponse)
async def health_check():
    import time
    return HealthResponse(uptime_seconds=time.time())
