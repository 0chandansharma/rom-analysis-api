# app/api/v1/endpoints/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.models.requests import FrameAnalysisRequest
from app.services.frame_analyzer import FrameAnalyzer
from app.api.dependencies import get_frame_analyzer
import json
import logging
from typing import Dict, Optional
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(data)

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    analyzer: FrameAnalyzer = Depends(get_frame_analyzer)
):
    """WebSocket endpoint for real-time ROM analysis"""
    logger.info(f"WebSocket connection attempt for session {session_id}")
    
    # Accept the connection first
    try:
        await websocket.accept()
        logger.info(f"WebSocket accepted for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket: {e}")
        return
    
    # Add to connection manager
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive frame data
            data = await websocket.receive_json()
            
            # Validate required fields
            if "frame_base64" not in data:
                await websocket.send_json({
                    "error": "frame_base64 is required"
                })
                continue
            
            if "body_part" not in data or "movement_type" not in data:
                await websocket.send_json({
                    "error": "body_part and movement_type are required"
                })
                continue
            
            try:
                # Analyze frame
                result = await analyzer.analyze(
                    frame_base64=data["frame_base64"],
                    session_id=session_id,
                    body_part=data["body_part"],
                    movement_type=data["movement_type"],
                    include_keypoints=data.get("include_keypoints", False),
                    include_visualization=False
                )
                
                # Send result back
                await websocket.send_json(result)
                
            except Exception as e:
                logger.error(f"Error analyzing frame for session {session_id}: {e}")
                await websocket.send_json({
                    "error": f"Analysis failed: {str(e)}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)

@router.websocket("/ws/stream/{session_id}")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    session_id: str,
    analyzer: FrameAnalyzer = Depends(get_frame_analyzer)
):
    """
    WebSocket endpoint for continuous streaming analysis
    Expects a stream of frames and continuously analyzes them
    """
    logger.info(f"WebSocket stream connection attempt for session {session_id}")
    
    # Accept the connection first
    try:
        await websocket.accept()
        logger.info(f"WebSocket stream accepted for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket stream: {e}")
        return
    
    # Add to connection manager
    await manager.connect(websocket, session_id)
    
    # Configuration for the stream
    body_part = None
    movement_type = None
    include_keypoints = False
    
    try:
        # First message should be configuration
        config_data = await websocket.receive_json()
        body_part = config_data.get("body_part")
        movement_type = config_data.get("movement_type")
        include_keypoints = config_data.get("include_keypoints", False)
        
        if not body_part or not movement_type:
            await websocket.send_json({
                "error": "First message must include body_part and movement_type"
            })
            return
        
        await websocket.send_json({
            "status": "ready",
            "config": {
                "body_part": body_part,
                "movement_type": movement_type,
                "include_keypoints": include_keypoints
            }
        })
        
        # Process incoming frames
        frame_count = 0
        while True:
            # Receive frame
            frame_data = await websocket.receive_text()
            
            # Handle control messages
            if frame_data == "ping":
                await websocket.send_text("pong")
                continue
            
            try:
                # Parse frame data if it's JSON
                if frame_data.startswith("{"):
                    data = json.loads(frame_data)
                    frame_base64 = data.get("frame")
                else:
                    # Assume it's just the base64 frame
                    frame_base64 = frame_data
                
                # Analyze frame
                result = await analyzer.analyze(
                    frame_base64=frame_base64,
                    session_id=session_id,
                    body_part=body_part,
                    movement_type=movement_type,
                    include_keypoints=include_keypoints,
                    include_visualization=False
                )
                
                # Add frame number
                result["frame_number"] = frame_count
                frame_count += 1
                
                # Send result
                await websocket.send_json(result)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"Error in stream analysis: {e}")
                await websocket.send_json({
                    "error": f"Analysis failed: {str(e)}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Stream ended for session {session_id} after {frame_count} frames")
    except Exception as e:
        logger.error(f"WebSocket stream error for session {session_id}: {e}")
        manager.disconnect(session_id)