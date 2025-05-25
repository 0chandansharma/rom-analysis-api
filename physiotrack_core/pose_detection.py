"""
Complete pose detection wrapper for PhysioTrack
Properly integrated with RTMLib
"""
import numpy as np
from typing import Dict, Tuple, List, Optional
import logging

try:
    from rtmlib import PoseTracker, BodyWithFeet, Body, Wholebody
    RTMLIB_AVAILABLE = True
except ImportError:
    RTMLIB_AVAILABLE = False
    logging.warning("RTMLib not available. Pose detection will not work.")

class PoseDetector:
    """Pose detector wrapper with proper RTMLib integration"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self, 
        model: str = "body_with_feet",
        mode: str = "performance",  # Changed default to performance
        device: str = "cpu",
        backend: str = "onnxruntime",
        det_frequency: int = 1
    ):
        # Avoid re-initialization
        if PoseDetector._initialized:
            return
            
        if not RTMLIB_AVAILABLE:
            raise ImportError("RTMLib is not installed. Please install it with: pip install rtmlib")
        
        self.model = model
        self.mode = mode
        self.device = device
        self.backend = backend
        
        # Model selection
        if model.lower() == "body_with_feet":
            self.ModelClass = BodyWithFeet
            self.keypoint_names = self._get_halpe26_keypoints()
        elif model.lower() == "whole_body":
            self.ModelClass = Wholebody
            self.keypoint_names = self._get_coco133_keypoints()
        elif model.lower() == "body":
            self.ModelClass = Body
            self.keypoint_names = self._get_coco17_keypoints()
        else:
            raise ValueError(f"Unknown model: {model}")
        
        # Initialize pose tracker
        try:
            self.tracker = PoseTracker(
                self.ModelClass,
                det_frequency=det_frequency,
                mode=mode,
                backend=backend,
                device=device,
                tracking=False,  # We'll handle tracking separately
                to_openpose=False
            )
            PoseDetector._initialized = True
            logging.info(f"Pose detector initialized with {model} model in {mode} mode on {device}")
        except Exception as e:
            logging.error(f"Failed to initialize pose tracker: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect poses in frame
        
        Args:
            frame: Input image (BGR format from cv2)
            
        Returns:
            Tuple of (keypoints, scores) arrays
            - keypoints: shape (n_persons, n_keypoints, 2)
            - scores: shape (n_persons, n_keypoints)
        """
        if not RTMLIB_AVAILABLE:
            return np.array([]), np.array([])
        
        try:
            # RTMLib returns keypoints and scores
            keypoints, scores = self.tracker(frame)
            
            # Ensure proper output format
            if len(keypoints) == 0:
                return np.array([]), np.array([])
            
            return keypoints, scores
        except Exception as e:
            logging.error(f"Pose detection failed: {e}")
            return np.array([]), np.array([])
    
    def keypoints_to_dict(
        self, 
        keypoints: np.ndarray, 
        scores: np.ndarray,
        confidence_threshold: float = 0.3
    ) -> Dict[str, np.ndarray]:
        """
        Convert keypoint array to dictionary with confidence filtering
        
        Args:
            keypoints: Array of shape (n_keypoints, 2)
            scores: Array of shape (n_keypoints,)
            confidence_threshold: Minimum confidence to include keypoint
            
        Returns:
            Dictionary mapping keypoint names to coordinates
        """
        result = {}
        
        for i, name in enumerate(self.keypoint_names):
            if i < len(scores) and scores[i] >= confidence_threshold:
                result[name] = keypoints[i]
        
        # Add computed keypoints (Neck and Hip)
        if "Neck" not in result and all(k in result for k in ["LShoulder", "RShoulder"]):
            result["Neck"] = (result["LShoulder"] + result["RShoulder"]) / 2
        
        if "Hip" not in result and all(k in result for k in ["LHip", "RHip"]):
            result["Hip"] = (result["LHip"] + result["RHip"]) / 2
        
        return result
    
    def _get_halpe26_keypoints(self) -> List[str]:
        """HALPE_26 keypoint names"""
        return [
            "Nose", "LEye", "REye", "LEar", "REar",
            "LShoulder", "RShoulder", "LElbow", "RElbow",
            "LWrist", "RWrist", "LHip", "RHip",
            "LKnee", "RKnee", "LAnkle", "RAnkle",
            "Head", "Neck", "Hip", "LBigToe", "RBigToe",
            "LSmallToe", "RSmallToe", "LHeel", "RHeel"
        ]
    
    def _get_coco17_keypoints(self) -> List[str]:
        """COCO_17 keypoint names"""
        return [
            "Nose", "LEye", "REye", "LEar", "REar",
            "LShoulder", "RShoulder", "LElbow", "RElbow",
            "LWrist", "RWrist", "LHip", "RHip",
            "LKnee", "RKnee", "LAnkle", "RAnkle"
        ]
    
    def _get_coco133_keypoints(self) -> List[str]:
        """COCO_133 keypoint names (simplified - main body only)"""
        return self._get_halpe26_keypoints()
    
    @property
    def is_initialized(self) -> bool:
        """Check if detector is properly initialized"""
        return PoseDetector._initialized and hasattr(self, 'tracker')