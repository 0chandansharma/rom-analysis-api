from fastapi import APIRouter, HTTPException, Depends
from app.services.session_manager import SessionManager
from app.api.dependencies import get_session_manager

router = APIRouter()

@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get session ROM data"""
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_data

@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Clear session data"""
    await session_manager.clear_session(session_id)
    return {"message": "Session cleared"}