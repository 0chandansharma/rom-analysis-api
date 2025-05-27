# app/api/v1/endpoints/analyze_optimized.py
from fastapi import APIRouter, File, Form, UploadFile, Depends
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64  # Add this import!
from app.services.frame_analyzer import FrameAnalyzer
from app.api.dependencies import get_frame_analyzer

router = APIRouter()

@router.post("/frame")
async def analyze_frame_optimized(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    body_part: str = Form(...),
    movement_type: str = Form(...),
    include_keypoints: bool = Form(False),
    analyzer: FrameAnalyzer = Depends(get_frame_analyzer)
):
    """Analyze frame from file upload (no base64 encoding)"""
    
    try:
        # Read file directly
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid image file"}
            )
        
        # Convert frame to base64 for existing analyzer
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Process frame
        result = await analyzer.analyze(
            frame_base64=frame_base64,
            session_id=session_id,
            body_part=body_part,
            movement_type=movement_type,
            include_keypoints=include_keypoints
        )
        
        return result
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing failed: {str(e)}"}
        )