"""
Simplified pose detection wrapper for PhysioTrack
Extract only the essential parts from physiotrack/process.py
"""
import numpy as np
from typing import Dict, Tuple, List, Optional
from rtmlib import PoseTracker, BodyWithFeet, Body, Wholebody

class PoseDetector:
    """Simplified pose detector wrapper"""
    
    def __init__(
        self, 
        model: str = "body_with_feet",
        mode: str = "lightweight",
        device: str = "cpu",
        backend: str = "onnxruntime"
    ):
        # Model selection
        if model.lower() == "body_with_feet":
            ModelClass = BodyWithFeet
            self.keypoint_names = self._get_halpe26_keypoints()
        elif model.lower() == "whole_body":
            ModelClass = Wholebody
            self.keypoint_names = self._get_coco133_keypoints()
        elif model.lower() == "body":
            ModelClass = Body
            self.keypoint_names = self._get_coco17_keypoints()
        else:
            raise ValueError(f"Unknown model: {model}")
        
        # Initialize pose tracker
        self.tracker = PoseTracker(
            ModelClass,
            det_frequency=1,
            mode=mode,
            backend=backend,
            device=device,
            tracking=False,
            to_openpose=False
        )
    
    def detect(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect poses in frame
        Returns: (keypoints, scores) arrays
        """
        return self.tracker(frame)
    
    def keypoints_to_dict(
        self, 
        keypoints: np.ndarray, 
        scores: np.ndarray,
        valid_mask: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """Convert keypoint array to dictionary"""
        result = {}
        for i, name in enumerate(self.keypoint_names):
            if valid_mask is None or valid_mask[i]:
                result[name] = keypoints[i]
        
        # Add computed keypoints
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
        """COCO_133 keypoint names (simplified)"""
        # Return main body keypoints only for now
        return self._get_halpe26_keypoints()