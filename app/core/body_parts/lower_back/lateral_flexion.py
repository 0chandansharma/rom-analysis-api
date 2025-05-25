import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import calculate_angle_between_points

class LowerBackLateralFlexion(Movement):
    """Lower back lateral flexion (side bending) analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_lateral_flexion"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["Neck", "Hip", "LShoulder", "RShoulder", "LHip", "RHip"]
    
    @property
    def primary_angle(self) -> str:
        return "lateral_trunk"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (-30, 30)  # Negative for left, positive for right
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate lateral flexion angle"""
        angles = {}
        
        # Calculate trunk lateral angle
        if all(k in keypoints for k in ["Neck", "Hip"]):
            trunk_vector = keypoints["Neck"] - keypoints["Hip"]
            # Calculate deviation from vertical
            lateral_angle = np.degrees(np.arctan2(trunk_vector[0], -trunk_vector[1]))
            angles["lateral_trunk"] = lateral_angle
        
        # Calculate shoulder tilt
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_angle = calculate_angle_between_points(
                keypoints["LShoulder"],
                keypoints["RShoulder"],
                reference="horizontal"
            )
            angles["shoulder_tilt"] = shoulder_angle
        
        return angles
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate position for lateral flexion"""
        # Check basic requirements
        valid, message = super().validate_position(keypoints)
        if not valid:
            return valid, message
        
        # Person should be facing camera
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            if shoulder_width < 50:
                return False, "Please face the camera directly"
        
        return True, "Position is correct"