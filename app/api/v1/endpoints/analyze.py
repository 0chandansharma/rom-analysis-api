from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from app.models.requests import FrameAnalysisRequest
from app.services.frame_analyzer import FrameAnalyzer
from app.api.dependencies import get_frame_analyzer

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze", response_class=JSONResponse)
async def analyze_frame(
    request: FrameAnalysisRequest,
    analyzer: FrameAnalyzer = Depends(get_frame_analyzer)
) -> Dict[str, Any]:
    """Analyze a single frame for ROM"""
    try:
        logger.info(f"Received analysis request for session {request.session_id}")
        logger.debug(f"Request details: body_part={request.body_part}, movement_type={request.movement_type}")
        
        # Validate request
        if not request.frame_base64:
            logger.error("Empty frame_base64 received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="frame_base64 cannot be empty"
            )
        
        logger.info("Starting frame analysis...")
        
        # Perform analysis
        result = await analyzer.analyze(
            frame_base64=request.frame_base64,
            session_id=request.session_id,
            body_part=request.body_part,
            movement_type=request.movement_type,
            include_keypoints=request.include_keypoints,
            include_visualization=request.include_visualization
        )
        
        logger.info(f"Analysis completed for session {request.session_id}")
        logger.debug(f"Result type: {type(result)}, Result: {result}")
        
        # Ensure result is not None
        if result is None:
            logger.error("Analyzer returned None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Analysis returned no result"
            )
        
        # Return the result directly
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {type(e).__name__}: {e}")
        # Log the full traceback for debugging
        import traceback
        logger.error(traceback.format_exc())
        
        # Return a proper error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )