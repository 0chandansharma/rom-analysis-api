import base64
import cv2
import numpy as np
import uuid
from typing import Dict, Optional, List
from datetime import datetime
import logging
import time

from app.core.pose.processor import PoseProcessor
from app.core.body_parts.registry import MovementRegistry
from app.core.rom.tracker import ROMTracker
from app.services.session_manager import SessionManager
from app.services.image_processor import ImageProcessor
from app.models.responses import AnalysisResponse, ROMData
from app.utils.exceptions import AnalysisError
from physiotrack_core.rom_calculations import ROMCalculator

logger = logging.getLogger(__name__)

class FrameAnalyzer:
    """Main service for analyzing frames - returns only JSON data"""
    
    def __init__(self, session_manager: SessionManager):
        self.pose_processor = PoseProcessor()
        self.session_manager = session_manager
        self.image_processor = ImageProcessor()
        
        # Check if pose processor is initialized
        if not self.pose_processor.is_initialized:
            raise RuntimeError("Pose processor failed to initialize")
    
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
        
        logger.info(f"Starting analysis for {body_part} - {movement_type}")
        start_time = time.time()
        
        # Validate movement is supported
        if not MovementRegistry.is_registered(body_part, movement_type):
            # Fall back to ROMCalculator if not in registry
            if body_part not in ROMCalculator.MOVEMENT_ANGLES:
                raise AnalysisError(f"Unsupported body part: {body_part}")
            if movement_type not in ROMCalculator.MOVEMENT_ANGLES[body_part]:
                raise AnalysisError(f"Unsupported movement for {body_part}: {movement_type}")
        
        # Decode frame
        try:
            frame = self.image_processor.decode_base64(frame_base64)
            logger.info(f"Frame decoded successfully: shape={frame.shape}")
        except Exception as e:
            logger.error(f"Failed to decode frame: {e}")
            raise AnalysisError(f"Failed to decode frame: {str(e)}")
        
        # Detect pose
        try:
            keypoints, confidence = self.pose_processor.process_frame(frame)
            logger.info(f"Pose detection complete: {len(keypoints)} keypoints, confidence={confidence}")
        except Exception as e:
            logger.error(f"Pose detection failed: {e}")
            keypoints, confidence = {}, 0.0
        
        # Generate frame ID
        frame_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
        
        if not keypoints:
            return self._create_no_pose_response(
                frame_id, session_id, body_part, movement_type
            )
        
        # Try to use MovementRegistry first
        try:
            if MovementRegistry.is_registered(body_part, movement_type):
                # Use registered movement class
                movement_class = MovementRegistry.get_movement(body_part, movement_type)
                movement = movement_class()
                
                # Validate position
                valid, message = movement.validate_position(keypoints)
                if not valid:
                    return self._create_invalid_position_response(
                        frame_id, session_id, body_part, movement_type, message, confidence
                    )
                
                # Calculate angles
                angles = movement.calculate_angles(keypoints)
                primary_angle_key = movement.primary_angle
                normal_range = movement.normal_range
                
                # Get max range from ROMCalculator
                movement_config = ROMCalculator.MOVEMENT_ANGLES.get(body_part, {}).get(movement_type, {})
                max_range = movement_config.get('max_range', normal_range)
            else:
                # Fallback to ROMCalculator
                angles = ROMCalculator.calculate_movement_angles(
                    keypoints, body_part, movement_type
                )
                movement_config = ROMCalculator.MOVEMENT_ANGLES[body_part][movement_type]
                primary_angle_key = movement_config.get('primary', 'trunk')
                normal_range = movement_config['normal_range']
                max_range = movement_config['max_range']
                
        except ValueError as e:
            raise AnalysisError(str(e))
        
        # Get or create ROM tracker
        tracker = await self.session_manager.get_or_create_tracker(
            session_id, body_part, movement_type
        )
        
        # Update ROM with primary angle
        primary_angle_value = angles.get(primary_angle_key, 0)
        rom_data = tracker.update(angles, primary_angle_key)
        
        # Validate ROM
        validation = ROMCalculator.validate_rom(
            primary_angle_value, body_part, movement_type
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
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
                "normal_range": list(validation['normal_range']),
                "max_range": list(validation['max_range'])
            },
            "frame_metrics": {
                "keypoints_detected": len(keypoints),
                "angles_calculated": len(angles),
                "processing_time_ms": round(processing_time_ms, 2)
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
        
        # Save tracker state
        await self.session_manager.save_tracker(session_id, tracker)
        
        logger.info(f"Analysis complete: {len(angles)} angles calculated")
        
        # Ensure we always return a dictionary
        if not isinstance(response_data, dict):
            logger.error(f"Response data is not a dict: {type(response_data)}")
            return {"error": "Invalid response data type"}
        
        return response_data
    
    def _create_no_pose_response(
        self, 
        frame_id: str, 
        session_id: str, 
        body_part: str, 
        movement_type: str
    ) -> Dict:
        """Create response when no pose is detected"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "frame_id": frame_id,
            "body_part": body_part,
            "movement_type": movement_type,
            "pose_detected": False,
            "message": "No person detected in frame",
            "angles": {},
            "rom": {"current": 0, "min": 0, "max": 0, "range": 0},
            "pose_confidence": 0.0,
            "validation": {
                "in_normal_range": False,
                "in_max_range": False,
                "message": "No pose detected",
                "normal_range": [0, 0],
                "max_range": [0, 0]
            },
            "guidance": {
                "instruction": "Please ensure you are visible in the camera",
                "feedback": "No person detected",
                "improvement": "Move into the camera view"
            },
            "frame_metrics": {
                "keypoints_detected": 0,
                "angles_calculated": 0,
                "processing_time_ms": 0
            }
        }
    
    def _create_invalid_position_response(
        self,
        frame_id: str,
        session_id: str,
        body_part: str,
        movement_type: str,
        message: str,
        confidence: float
    ) -> Dict:
        """Create response when position is invalid"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "frame_id": frame_id,
            "body_part": body_part,
            "movement_type": movement_type,
            "pose_detected": True,
            "message": message,
            "angles": {},
            "rom": {"current": 0, "min": 0, "max": 0, "range": 0},
            "pose_confidence": round(confidence, 3),
            "validation": {
                "in_normal_range": False,
                "in_max_range": False,
                "message": message,
                "normal_range": [0, 0],
                "max_range": [0, 0]
            },
            "guidance": {
                "instruction": "Adjust your position",
                "feedback": message,
                "improvement": "Follow the positioning instructions"
            },
            "frame_metrics": {
                "keypoints_detected": 0,
                "angles_calculated": 0,
                "processing_time_ms": 0
            }
        }
    
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
        if body_part == "lower_back":
            if movement_type == "flexion":
                if current_angle < 10:
                    guidance["instruction"] = "Bend forward slowly from your hips"
                    guidance["improvement"] = "Try to increase your forward bend"
                elif current_angle > 60:
                    guidance["instruction"] = "You've reached good flexion"
                    guidance["improvement"] = "Hold this position or slowly return"
                else:
                    guidance["instruction"] = "Good position, continue the movement"
                    guidance["improvement"] = "Maintain smooth, controlled motion"
            
            elif movement_type == "extension":
                if current_angle > -5:
                    guidance["instruction"] = "Lean backward slowly"
                    guidance["improvement"] = "Engage your core for support"
                elif current_angle < -30:
                    guidance["instruction"] = "Maximum extension reached"
                    guidance["improvement"] = "Don't push beyond comfort"
                else:
                    guidance["instruction"] = "Good extension position"
                    guidance["improvement"] = "Keep the movement controlled"
            
            elif movement_type == "lateral_flexion":
                if abs(current_angle) < 5:
                    guidance["instruction"] = "Bend sideways from your waist"
                    guidance["improvement"] = "Keep your body in one plane"
                elif abs(current_angle) > 30:
                    guidance["instruction"] = "Good lateral flexion achieved"
                    guidance["improvement"] = "Try the other side for balance"
                else:
                    guidance["instruction"] = "Continue the side bend"
                    guidance["improvement"] = "Keep shoulders and hips aligned"
            
            elif movement_type == "rotation":
                if abs(current_angle) < 10:
                    guidance["instruction"] = "Rotate your upper body"
                    guidance["improvement"] = "Keep hips facing forward"
                elif abs(current_angle) > 45:
                    guidance["instruction"] = "Maximum rotation reached"
                    guidance["improvement"] = "Hold briefly, then return"
                else:
                    guidance["instruction"] = "Good rotation angle"
                    guidance["improvement"] = "Maintain controlled movement"
        
        # Add more body parts guidance as needed
        
        return guidance