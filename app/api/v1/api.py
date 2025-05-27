# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import analyze, session, health, test, analyze_optimized

api_router = APIRouter()

api_router.include_router(analyze.router, prefix="/analyze", tags=["analysis"])
api_router.include_router(analyze_optimized.router, prefix="/analyze", tags=["analysis"])  # Add this
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(test.router, prefix="/test", tags=["test"])

# from fastapi import APIRouter
# from app.api.v1.endpoints import analyze, session, health, test

# api_router = APIRouter()

# api_router.include_router(analyze.router, prefix="/analyze", tags=["analysis"])
# api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
# api_router.include_router(health.router, prefix="/health", tags=["health"])
# api_router.include_router(test.router, prefix="/test", tags=["test"])

# # WebSocket routes are now mounted directly in main.py to avoid prefix issues