import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import calculate_angle_between_points

class LowerBackExtension(Movement):
    """Lower back extension movement analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_extension"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["Neck", "Hip", "LHip", "RHip", "LShoulder", "RShoulder"]
    
    @property
    def primary_angle(self) -> str:
        return "trunk"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (-30, 0)  # Normal extension range (negative values)
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate trunk and pelvis angles for extension"""
        angles = {}
        
        # Calculate trunk angle
        if all(k in keypoints for k in ["Neck", "Hip"]):
            trunk_angle = calculate_angle_between_points(
                keypoints["Neck"], 
                keypoints["Hip"],
                reference="vertical"
            )
            # Transform for extension (angle - 180)
            angles["trunk"] = trunk_angle - 180
        
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
        """Validate position for extension measurement"""
        valid, message = super().validate_position(keypoints)
        if not valid:
            return valid, message
        
        # Additional check for extension: trunk should be relatively upright
        if "trunk" in self.calculate_angles(keypoints):
            trunk_angle = self.calculate_angles(keypoints)["trunk"]
            if trunk_angle > 30:  # Too much flexion
                return False, "Please stand upright before extending"
        
        return True, "Position is correct"