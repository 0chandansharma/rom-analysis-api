from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
import numpy as np

class Movement(ABC):
    """Abstract base class for all movements"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Movement name"""
        pass
    
    @property
    @abstractmethod
    def required_keypoints(self) -> List[str]:
        """List of required keypoint names"""
        pass
    
    @property
    @abstractmethod
    def primary_angle(self) -> str:
        """Primary angle name for this movement"""
        pass
    
    @property
    @abstractmethod
    def normal_range(self) -> Tuple[float, float]:
        """Normal ROM range (min, max) in degrees"""
        pass
    
    @abstractmethod
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate all angles for this movement"""
        pass
    
    @abstractmethod
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate if the position is correct for this movement"""
        pass
    
    def get_movement_phase(self, angle: float) -> str:
        """Determine movement phase based on angle"""
        min_range, max_range = self.normal_range
        if angle < min_range:
            return "below_normal"
        elif angle > max_range:
            return "above_normal"
        else:
            return "normal"