import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import calculate_angle_between_points

class LowerBackFlexion(Movement):
    """Lower back flexion movement analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_flexion"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["Neck", "Hip", "LHip", "RHip", "LShoulder", "RShoulder"]
    
    @property
    def primary_angle(self) -> str:
        return "trunk"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (0, 60)  # Normal flexion range
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate trunk and pelvis angles for flexion"""
        angles = {}
        
        # Calculate trunk angle (Neck to Hip)
        if all(k in keypoints for k in ["Neck", "Hip"]):
            trunk_vector = keypoints["Hip"] - keypoints["Neck"]
            trunk_angle = calculate_angle_between_points(
                keypoints["Neck"], 
                keypoints["Hip"],
                reference="vertical"
            )
            # Transform for flexion (180 - angle)
            angles["trunk"] = 180 - trunk_angle
        
        # Calculate pelvis angle
        if all(k in keypoints for k in ["LHip", "RHip"]):
            pelvis_angle = calculate_angle_between_points(
                keypoints["LHip"],
                keypoints["RHip"],
                reference="horizontal"
            )
            angles["pelvis"] = pelvis_angle
        
        return angles
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate if person is in correct position for flexion measurement"""
        # Check if person is facing camera (frontal plane)
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            # If shoulders are too close, person might be sideways
            if shoulder_width < 50:  # pixels, adjust threshold as needed
                return False, "Please face the camera directly"
        
        # Check if all required keypoints are visible
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        return True, "Position is correct"