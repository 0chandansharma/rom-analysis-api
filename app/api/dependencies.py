from app.services.frame_analyzer import FrameAnalyzer
from app.services.session_manager import SessionManager
from app.storage.memory import InMemoryStorage

# Singleton instances
_storage = InMemoryStorage()
_session_manager = SessionManager(_storage)
_frame_analyzer = FrameAnalyzer(_session_manager)

def get_frame_analyzer() -> FrameAnalyzer:
    """Dependency for frame analyzer"""
    return _frame_analyzer

def get_session_manager() -> SessionManager:
    """Dependency for session manager"""
    return _session_manager