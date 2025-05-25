from fastapi import APIRouter
from app.api.v1.endpoints import analyze, session, health, test

api_router = APIRouter()

api_router.include_router(analyze.router, prefix="/analyze", tags=["analysis"])
api_router.include_router(session.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(test.router, prefix="/test", tags=["test"])

# Import and include websocket routes separately to avoid prefix issues
from app.api.v1.endpoints import websocket
api_router.include_router(websocket.router, tags=["websocket"])