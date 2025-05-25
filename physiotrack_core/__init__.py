"""
Simplified PhysioTrack core for API usage
"""
from .pose_detection import PoseDetector
from .angle_computation import calculate_angle_between_points

__all__ = ['PoseDetector', 'calculate_angle_between_points']