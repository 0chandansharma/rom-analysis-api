# app/models/responses.py - Updated
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime

class KeypointData(BaseModel):
    x: float
    y: float

class ValidationData(BaseModel):
    in_normal_range: bool
    in_max_range: bool
    message: str
    normal_range: List[float]
    max_range: List[float]

class GuidanceData(BaseModel):
    instruction: str
    feedback: str
    improvement: str

class FrameMetrics(BaseModel):
    keypoints_detected: int
    angles_calculated: int
    processing_time_ms: float

class ROMData(BaseModel):
    current: float
    min: float
    max: float
    range: float

class AnalysisResponse(BaseModel):
    timestamp: datetime
    frame_id: str
    body_part: str
    movement_type: str
    pose_detected: bool
    angles: Dict[str, float]
    rom: ROMData
    pose_confidence: float
    validation: ValidationData
    guidance: GuidanceData
    frame_metrics: FrameMetrics
    keypoints: Optional[Dict[str, KeypointData]] = None
    skeleton_connections: Optional[List[List[str]]] = None
    message: Optional[str] = None