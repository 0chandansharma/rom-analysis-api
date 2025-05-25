# ===== app/core/body_parts/lower_back/rotation.py =====
import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import add_virtual_keypoints
from physiotrack_core.rom_calculations import calculate_lower_back_rotation as calc_rotation

class LowerBackRotation(Movement):
    """Lower back rotation analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_rotation"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["LShoulder", "RShoulder", "LHip", "RHip", "Neck", "Hip"]
    
    @property
    def primary_angle(self) -> str:
        return "trunk_rotation"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (-45, 45)  # Negative for left rotation, positive for right
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate rotation angle based on shoulder and hip alignment"""
        keypoints = add_virtual_keypoints(keypoints)
        return calc_rotation(keypoints)
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate position for rotation measurement"""
        # Basic validation
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Check if person is reasonably upright
        if all(k in keypoints for k in ["Neck", "Hip"]):
            trunk_vector = keypoints["Neck"] - keypoints["Hip"]
            trunk_angle = np.degrees(np.arctan2(abs(trunk_vector[0]), -trunk_vector[1]))
            
            if trunk_angle > 30:
                return False, "Please stand more upright for rotation measurement"
        
        return True, "Position is correct"