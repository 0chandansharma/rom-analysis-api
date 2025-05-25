from typing import List
from pydantic_settings import BaseSettings
import torch

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "ROM Analysis API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Model Settings - Using best/performance model
    POSE_MODEL: str = "body_with_feet"
    POSE_MODE: str = "performance"  # Changed from lightweight to performance
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"  # Auto-detect GPU
    BACKEND: str = "onnxruntime"  # Best backend for performance
    
    # Processing Settings
    CONFIDENCE_THRESHOLD: float = 0.3
    MIN_KEYPOINTS_RATIO: float = 0.5
    ANGLE_SMOOTHING_WINDOW: int = 5
    
    # Storage Settings
    USE_REDIS: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    SESSION_TTL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"

settings = Settings()