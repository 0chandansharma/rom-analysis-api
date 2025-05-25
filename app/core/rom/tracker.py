from typing import Dict, Optional
import numpy as np
from collections import deque

class ROMTracker:
    """Track ROM data for a session"""
    
    def __init__(self, body_part: str, movement_type: str, window_size: int = 5):
        self.body_part = body_part
        self.movement_type = movement_type
        self.window_size = window_size
        
        # ROM tracking
        self.min_angle: Optional[float] = None
        self.max_angle: Optional[float] = None
        self.angle_history = deque(maxlen=window_size)
        
        # Frame counting
        self.frame_count = 0
        self.valid_frame_count = 0
        
    def update(self, angles: Dict[str, float], primary_angle_key: str) -> Dict[str, float]:
        """Update ROM with new angle measurements"""
        self.frame_count += 1
        
        if primary_angle_key not in angles:
            return self.get_current_rom()
        
        angle = angles[primary_angle_key]
        if np.isnan(angle):
            return self.get_current_rom()
        
        self.valid_frame_count += 1
        self.angle_history.append(angle)
        
        # Calculate smoothed angle
        smoothed_angle = np.mean(self.angle_history)
        
        # Update min/max
        if self.min_angle is None:
            self.min_angle = smoothed_angle
            self.max_angle = smoothed_angle
        else:
            self.min_angle = min(self.min_angle, smoothed_angle)
            self.max_angle = max(self.max_angle, smoothed_angle)
        
        return self.get_current_rom(current=smoothed_angle)
    
    def get_current_rom(self, current: Optional[float] = None) -> Dict[str, float]:
        """Get current ROM data"""
        if self.min_angle is None:
            return {
                "current": 0.0,
                "min": 0.0,
                "max": 0.0,
                "range": 0.0
            }
        
        current_angle = current if current is not None else (
            np.mean(self.angle_history) if self.angle_history else 0.0
        )
        
        return {
            "current": round(current_angle, 1),
            "min": round(self.min_angle, 1),
            "max": round(self.max_angle, 1),
            "range": round(self.max_angle - self.min_angle, 1)
        }
    
    def reset(self):
        """Reset ROM tracking"""
        self.min_angle = None
        self.max_angle = None
        self.angle_history.clear()
        self.frame_count = 0
        self.valid_frame_count = 0