from enum import Enum
from typing import Dict, List
from pydantic import BaseModel

class BodyPart(str, Enum):
    LOWER_BACK = "lower_back"
    SHOULDER = "shoulder"
    ELBOW = "elbow"
    HIP = "hip"
    KNEE = "knee"
    ANKLE = "ankle"

class MovementType(str, Enum):
    # Lower back movements
    FLEXION = "flexion"
    EXTENSION = "extension"
    LATERAL_FLEXION = "lateral_flexion"
    ROTATION = "rotation"
    
    # Joint movements
    ABDUCTION = "abduction"
    ADDUCTION = "adduction"
    INTERNAL_ROTATION = "internal_rotation"
    EXTERNAL_ROTATION = "external_rotation"
    
    # Ankle specific
    DORSIFLEXION = "dorsiflexion"
    PLANTARFLEXION = "plantarflexion"
    INVERSION = "inversion"
    EVERSION = "eversion"
    
    # Forearm specific
    PRONATION = "pronation"
    SUPINATION = "supination"

class PoseData(BaseModel):
    keypoints: Dict[str, List[float]]
    confidence: float
    detected_keypoints: List[str]
    missing_keypoints: List[str]

class AngleData(BaseModel):
    angles: Dict[str, float]
    primary_angle: str
    movement_phase: str