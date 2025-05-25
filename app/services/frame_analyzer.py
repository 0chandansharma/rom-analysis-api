import base64
import cv2
import numpy as np
import uuid
from typing import Dict, Optional
from datetime import datetime

from app.core.pose.processor import PoseProcessor
from app.core.body_parts.registry import MovementRegistry
from app.core.rom.tracker import ROMTracker
from app.services.session_manager import SessionManager
from app.services.image_processor import ImageProcessor
from app.models.responses import AnalysisResponse, ROMData
from app.utils.exceptions import AnalysisError
from physiotrack_core.rom_calculations import ROMCalculator

class FrameAnalyzer:
    """Main service for analyzing frames - returns only JSON data"""
    
    def __init__(self, session_manager: SessionManager):
        self.pose_processor = PoseProcessor()
        self.session_manager = session_manager
        self.image_processor = ImageProcessor()
    
    async def analyze(
        self,
        frame_base64: str,
        session_id: str,
        body_part: str,
        movement_type: str,
        include_keypoints: bool = False,
        include_visualization: bool = False  # Ignored - no visualization
    ) -> Dict:
        """Analyze a single frame and return JSON data only"""
        
        # Decode frame
        try:
            frame = self.image_processor.decode_base64(frame_base64)
        except Exception as e:
            raise AnalysisError(f"Failed to decode frame: {str(e)}")
        
        # Detect pose
        keypoints, confidence = self.pose_processor.process_frame(frame)
        if not keypoints:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "frame_id": f"{session_id}_{uuid.uuid4().hex[:8]}",
                "body_part": body_part,
                "movement_type": movement_type,
                "pose_detected": False,
                "message": "No person detected in frame",
                "angles": {},
                "rom": {"current": 0, "min": 0, "max": 0, "range": 0},
                "pose_confidence": 0.0
            }
        
        # Calculate angles using ROMCalculator
        try:
            angles = ROMCalculator.calculate_movement_angles(
                keypoints, body_part, movement_type
            )
        except ValueError as e:
            raise AnalysisError(str(e))
        
        # Get primary angle for ROM tracking
        movement_config = ROMCalculator.MOVEMENT_ANGLES.get(body_part, {}).get(movement_type, {})
        primary_angle_key = movement_config.get('primary', 'trunk')
        
        # Get or create ROM tracker
        tracker = await self.session_manager.get_or_create_tracker(
            session_id, body_part, movement_type
        )
        
        # Update ROM
        rom_data = tracker.update(angles, primary_angle_key)
        
        # Validate ROM
        primary_angle_value = angles.get(primary_angle_key, 0)
        validation = ROMCalculator.validate_rom(
            primary_angle_value, body_part, movement_type
        )
        
        # Generate frame ID
        frame_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        
        # Prepare response data
        response_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "frame_id": frame_id,
            "body_part": body_part,
            "movement_type": movement_type,
            "pose_detected": True,
            "angles": {k: round(v, 1) for k, v in angles.items()},
            "rom": rom_data,
            "pose_confidence": round(confidence, 3),
            "validation": {
                "in_normal_range": validation['in_normal_range'],
                "in_max_range": validation['in_max_range'],
                "message": validation['message'],
                "normal_range": validation['normal_range'],
                "max_range": validation['max_range']
            },
            "frame_metrics": {
                "keypoints_detected": len(keypoints),
                "angles_calculated": len(angles),
                "processing_time_ms": 0  # You can add timing if needed
            }
        }
        
        # Add keypoints if requested (for visualization in frontend)
        if include_keypoints:
            response_data["keypoints"] = {
                k: {"x": float(v[0]), "y": float(v[1])} 
                for k, v in keypoints.items()
            }
            
            # Add skeleton connections for frontend visualization
            response_data["skeleton_connections"] = self._get_skeleton_connections()
        
        # Add movement guidance
        response_data["guidance"] = self._get_movement_guidance(
            body_part, movement_type, primary_angle_value, validation
        )
        
        return response_data
    
    def _get_skeleton_connections(self) -> List[List[str]]:
        """Get skeleton connections for frontend visualization"""
        return [
            ["LShoulder", "RShoulder"],
            ["LShoulder", "LElbow"],
            ["LElbow", "LWrist"],
            ["RShoulder", "RElbow"],
            ["RElbow", "RWrist"],
            ["LShoulder", "LHip"],
            ["RShoulder", "RHip"],
            ["LHip", "RHip"],
            ["LHip", "LKnee"],
            ["LKnee", "LAnkle"],
            ["RHip", "RKnee"],
            ["RKnee", "RAnkle"],
            ["Neck", "Hip"],
            ["Neck", "Head"],
            ["LAnkle", "LBigToe"],
            ["RAnkle", "RBigToe"]
        ]
    
    def _get_movement_guidance(
        self,
        body_part: str,
        movement_type: str,
        current_angle: float,
        validation: Dict
    ) -> Dict[str, str]:
        """Generate movement guidance based on current position"""
        guidance = {
            "instruction": "",
            "feedback": validation['message'],
            "improvement": ""
        }
        
        # Movement-specific guidance
        if body_part == "lower_back" and movement_type == "flexion":
            if current_angle < 10:
                guidance["instruction"] = "Bend forward slowly from your hips"
                guidance["improvement"] = "Try to increase your forward bend"
            elif current_angle > 60:
                guidance["instruction"] = "You've reached good flexion"
                guidance["improvement"] = "Hold this position or slowly return"
            else:
                guidance["instruction"] = "Good position, continue the movement"
                guidance["improvement"] = "Maintain smooth, controlled motion"
        
        elif body_part == "lower_back" and movement_type == "extension":
            if current_angle > -5:
                guidance["instruction"] = "Lean backward slowly"
                guidance["improvement"] = "Engage your core for support"
            elif current_angle < -30:
                guidance["instruction"] = "Maximum extension reached"
                guidance["improvement"] = "Don't push beyond comfort"
            else:
                guidance["instruction"] = "Good extension position"
                guidance["improvement"] = "Keep the movement controlled"
        
        # Add more body parts and movements as needed
        
        return guidance