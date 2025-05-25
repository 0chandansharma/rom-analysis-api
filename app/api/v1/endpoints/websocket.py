# app/api/v1/endpoints/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.models.requests import FrameAnalysisRequest
from app.services.frame_analyzer import FrameAnalyzer
from app.services.session_manager import SessionManager
from app.storage.memory import InMemoryStorage
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
        """Note: WebSocket should already be accepted before calling this"""
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

# Create analyzer instance (singleton pattern already handled in FrameAnalyzer)
_storage = InMemoryStorage()
_session_manager = SessionManager(_storage)
_frame_analyzer = FrameAnalyzer(_session_manager)

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket endpoint for real-time ROM analysis"""
    logger.info(f"WebSocket connection attempt for session {session_id}")
    
    # Accept the connection
    try:
        await websocket.accept()
        logger.info(f"WebSocket accepted for session {session_id}")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket: {e}")
        return
    
    # Add to connection manager (don't accept again)
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            try:
                # Receive frame data with timeout
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                
                # Validate required fields
                if "frame_base64" not in data:
                    await websocket.send_json({
                        "error": "frame_base64 is required",
                        "status": "error"
                    })
                    continue
                
                if "body_part" not in data or "movement_type" not in data:
                    await websocket.send_json({
                        "error": "body_part and movement_type are required",
                        "status": "error"
                    })
                    continue
                
                try:
                    # Analyze frame
                    result = await _frame_analyzer.analyze(
                        frame_base64=data["frame_base64"],
                        session_id=session_id,
                        body_part=data["body_part"],
                        movement_type=data["movement_type"],
                        include_keypoints=data.get("include_keypoints", False),
                        include_visualization=False
                    )
                    
                    # Ensure result is a dict
                    if isinstance(result, dict):
                        result["status"] = "success"
                        await websocket.send_json(result)
                    else:
                        logger.error(f"Result is not a dict: {type(result)}")
                        await websocket.send_json({
                            "error": "Invalid result format",
                            "status": "error"
                        })
                    
                except Exception as e:
                    logger.error(f"Error analyzing frame for session {session_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    await websocket.send_json({
                        "error": f"Analysis failed: {str(e)}",
                        "status": "error"
                    })
                    
            except asyncio.TimeoutError:
                logger.warning(f"WebSocket timeout for session {session_id}")
                # Send ping to check if connection is alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        manager.disconnect(session_id)

@router.websocket("/ws/stream/{session_id}")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for continuous streaming analysis
    Expects a stream of frames and continuously analyzes them
    """
    logger.info(f"WebSocket stream connection attempt for session {session_id}")
    
    # Accept the connection
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
        # First message should be configuration (with timeout)
        try:
            config_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
            body_part = config_data.get("body_part")
            movement_type = config_data.get("movement_type")
            include_keypoints = config_data.get("include_keypoints", False)
            
            if not body_part or not movement_type:
                await websocket.send_json({
                    "error": "First message must include body_part and movement_type",
                    "status": "error"
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
            
        except asyncio.TimeoutError:
            await websocket.send_json({
                "error": "Timeout waiting for configuration",
                "status": "error"
            })
            return
        
        # Process incoming frames
        frame_count = 0
        while True:
            try:
                # Receive frame with timeout
                frame_data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle control messages
                if frame_data == "ping":
                    await websocket.send_text("pong")
                    continue
                
                try:
                    # Parse frame data if it's JSON
                    if frame_data.startswith("{"):
                        data = json.loads(frame_data)
                        frame_base64 = data.get("frame", data.get("frame_base64"))
                    else:
                        # Assume it's just the base64 frame
                        frame_base64 = frame_data
                    
                    if not frame_base64:
                        await websocket.send_json({
                            "error": "No frame data provided",
                            "status": "error"
                        })
                        continue
                    
                    # Analyze frame
                    result = await _frame_analyzer.analyze(
                        frame_base64=frame_base64,
                        session_id=session_id,
                        body_part=body_part,
                        movement_type=movement_type,
                        include_keypoints=include_keypoints,
                        include_visualization=False
                    )
                    
                    # Add frame number and status
                    if isinstance(result, dict):
                        result["frame_number"] = frame_count
                        result["status"] = "success"
                        frame_count += 1
                        
                        # Send result
                        await websocket.send_json(result)
                    else:
                        await websocket.send_json({
                            "error": "Invalid result format",
                            "status": "error"
                        })
                    
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "error": "Invalid JSON format",
                        "status": "error"
                    })
                except Exception as e:
                    logger.error(f"Error in stream analysis: {e}")
                    await websocket.send_json({
                        "error": f"Analysis failed: {str(e)}",
                        "status": "error"
                    })
                    
            except asyncio.TimeoutError:
                logger.warning(f"Stream timeout for session {session_id}")
                # Send ping to check if connection is alive
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"Stream ended for session {session_id} after {frame_count} frames")
    except Exception as e:
        logger.error(f"WebSocket stream error for session {session_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        manager.disconnect(session_id)