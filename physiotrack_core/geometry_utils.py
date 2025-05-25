"""
Geometric utility functions from PhysioTrack
"""
import numpy as np
from typing import List, Tuple, Optional

def euclidean_distance(q1: np.ndarray, q2: np.ndarray) -> float:
    """
    Euclidean distance between 2 points (N-dim)
    """
    q1 = np.array(q1)
    q2 = np.array(q2)
    dist = q2 - q1
    
    if np.isnan(dist).all():
        return np.inf
    
    if len(dist.shape) == 1:
        euc_dist = np.sqrt(np.nansum([d**2 for d in dist]))
    else:
        euc_dist = np.sqrt(np.nansum([d**2 for d in dist], axis=1))
    
    return float(euc_dist)

def angle_2d_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Angle between two 2D vectors
    """
    v1_norm = v1 / (np.linalg.norm(v1) + 1e-6)
    v2_norm = v2 / (np.linalg.norm(v2) + 1e-6)
    
    cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))
    
    # Get signed angle
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    if cross < 0:
        angle = -angle
    
    return float(angle)

def project_point_to_line(point: np.ndarray, line_start: np.ndarray, line_end: np.ndarray) -> np.ndarray:
    """
    Project a point onto a line segment
    """
    line_vec = line_end - line_start
    point_vec = point - line_start
    line_len = np.linalg.norm(line_vec)
    
    if line_len == 0:
        return line_start
    
    line_unitvec = line_vec / line_len
    proj_length = np.dot(point_vec, line_unitvec)
    
    # Clamp to line segment
    proj_length = np.clip(proj_length, 0, line_len)
    
    return line_start + proj_length * line_unitvec

def angle_between_lines(line1_start: np.ndarray, line1_end: np.ndarray,
                       line2_start: np.ndarray, line2_end: np.ndarray) -> float:
    """
    Angle between two lines
    """
    v1 = line1_end - line1_start
    v2 = line2_end - line2_start
    
    return angle_2d_vectors(v1, v2)