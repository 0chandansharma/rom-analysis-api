# ===== app/core/body_parts/lower_back/lateral_flexion.py =====
import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import add_virtual_keypoints
from physiotrack_core.rom_calculations import calculate_lower_back_lateral_flexion as calc_lateral

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
        return "trunk"  # Will use lateral trunk angle
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (-30, 30)  # Negative for left, positive for right
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate lateral flexion angle"""
        keypoints = add_virtual_keypoints(keypoints)
        return calc_lateral(keypoints)
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate position for lateral flexion"""
        # Check basic requirements
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Person should be facing camera
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            if shoulder_width < 50:
                return False, "Please face the camera directly"
        
        return True, "Position is correct"
