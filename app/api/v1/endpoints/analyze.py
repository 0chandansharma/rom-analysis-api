from fastapi import APIRouter, HTTPException, Depends
from app.models.requests import FrameAnalysisRequest
from app.models.responses import AnalysisResponse
from app.services.frame_analyzer import FrameAnalyzer
from app.api.dependencies import get_frame_analyzer

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_frame(
    request: FrameAnalysisRequest,
    analyzer: FrameAnalyzer = Depends(get_frame_analyzer)
):
    """Analyze a single frame for ROM"""
    try:
        result = await analyzer.analyze(
            frame_base64=request.frame_base64,
            session_id=request.session_id,
            body_part=request.body_part,
            movement_type=request.movement_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")