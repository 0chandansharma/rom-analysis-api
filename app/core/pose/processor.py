import numpy as np
from typing import Dict, Tuple, Optional, List
from physiotrack_core.pose_detection import PoseDetector
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class PoseProcessor:
    """Process frames for pose detection with singleton pattern"""
    
    _instance = None
    _detector = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._detector = PoseDetector(
                    model=settings.POSE_MODEL,
                    mode=settings.POSE_MODE,
                    device=settings.DEVICE,
                    backend=settings.BACKEND
                )
                logger.info(f"PoseProcessor initialized with {settings.POSE_MODEL} model")
            except Exception as e:
                logger.error(f"Failed to initialize PoseDetector: {e}")
                raise
        return cls._instance
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Dict[str, np.ndarray], float]:
        """
        Process a single frame and return keypoints
        
        Args:
            frame: Input image as numpy array (BGR format)
            
        Returns:
            Tuple of (keypoints_dict, confidence_score)
        """
        if self._detector is None:
            logger.error("PoseDetector not initialized")
            return {}, 0.0
        
        # Detect pose
        try:
            keypoints, scores = self._detector.detect(frame)
        except Exception as e:
            logger.error(f"Pose detection failed: {e}")
            return {}, 0.0
        
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
            confidence_threshold=settings.CONFIDENCE_THRESHOLD
        )
        
        # Calculate average confidence
        avg_confidence = np.mean(person_scores[valid_mask]) if np.sum(valid_mask) > 0 else 0.0
        
        return keypoint_dict, float(avg_confidence)
    
    def validate_keypoints_for_movement(
        self, 
        keypoints: Dict[str, np.ndarray], 
        required_keypoints: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate if all required keypoints are present for a movement
        
        Args:
            keypoints: Dictionary of detected keypoints
            required_keypoints: List of required keypoint names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        missing_keypoints = [kp for kp in required_keypoints if kp not in keypoints]
        
        if missing_keypoints:
            return False, f"Missing keypoints: {', '.join(missing_keypoints)}"
        
        return True, "All required keypoints detected"
    
    @property
    def is_initialized(self) -> bool:
        """Check if pose processor is properly initialized"""
        return self._detector is not None and self._detector.is_initialized