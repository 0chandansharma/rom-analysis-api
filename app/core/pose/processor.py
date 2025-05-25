import numpy as np
from typing import Dict, Tuple, Optional
from physiotrack_core.pose_detection import PoseDetector
from app.config import settings

class PoseProcessor:
    """Process frames for pose detection"""
    
    _instance = None
    _detector = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._detector = PoseDetector(
                model=settings.POSE_MODEL,
                mode=settings.POSE_MODE,
                device=settings.DEVICE,
                backend=settings.BACKEND
            )
        return cls._instance
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Dict[str, np.ndarray], float]:
        """
        Process a single frame and return keypoints
        
        Returns:
            Tuple of (keypoints_dict, confidence_score)
        """
        # Detect pose
        keypoints, scores = self._detector.detect(frame)
        
        if len(keypoints) == 0:
            return {}, 0.0
        
        # Take first person detected
        person_keypoints = keypoints[0]
        person_scores = scores[0]
        
        # Filter by confidence threshold
        valid_mask = person_scores >= settings.CONFIDENCE_THRESHOLD
        
        # Check if enough keypoints are detected
        valid_ratio = np.sum(valid_mask) / len(person_scores)
        if valid_ratio < settings.MIN_KEYPOINTS_RATIO:
            return {}, valid_ratio
        
        # Convert to dictionary
        keypoint_dict = self._detector.keypoints_to_dict(
            person_keypoints, 
            person_scores,
            valid_mask
        )
        
        avg_confidence = np.mean(person_scores[valid_mask])
        
        return keypoint_dict, avg_confidence