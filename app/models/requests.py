from pydantic import BaseModel, Field

class FrameAnalysisRequest(BaseModel):
    frame_base64: str = Field(..., description="Base64 encoded image")
    session_id: str = Field(..., description="Unique session identifier")
    body_part: str = Field(..., description="Body part to analyze")
    movement_type: str = Field(..., description="Type of movement")
    include_keypoints: bool = Field(False, description="Include keypoints in response")
    include_visualization: bool = Field(False, description="Include visual feedback")