import logging
from typing import Optional
from threading import Lock

logger = logging.getLogger(__name__)

class ModelManager:
    """Singleton manager for pose detection model"""
    
    _initialized: bool = False
    _lock = Lock()
    
    @classmethod
    def initialize(cls):
        """Initialize the pose detection model"""
        with cls._lock:
            if not cls._initialized:
                try:
                    # Import here to avoid circular imports
                    from app.core.pose.processor import PoseProcessor
                    
                    # Create instance to load model
                    _ = PoseProcessor()
                    
                    cls._initialized = True
                    logger.info("Pose detection model initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize pose model: {e}")
                    raise
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if model is initialized"""
        return cls._initialized