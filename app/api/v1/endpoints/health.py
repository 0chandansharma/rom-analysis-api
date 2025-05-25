from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check - verify model is loaded"""
    from app.core.pose.model_manager import ModelManager
    
    model_ready = ModelManager.is_initialized()
    return {
        "status": "ready" if model_ready else "not_ready",
        "model_loaded": model_ready,
        "timestamp": datetime.utcnow().isoformat()
    }