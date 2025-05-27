# app/api/v1/endpoints/batch.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Dict
import uuid

router = APIRouter()

# In-memory job storage (use Redis in production)
processing_jobs = {}

@router.post("/batch/submit")
async def submit_batch(
    frames: List[str],  # Base64 frames
    session_id: str,
    body_part: str,
    movement_type: str,
    background_tasks: BackgroundTasks
):
    """Submit batch of frames for processing"""
    job_id = str(uuid.uuid4())
    
    # Store job info
    processing_jobs[job_id] = {
        "status": "pending",
        "total_frames": len(frames),
        "processed_frames": 0,
        "results": []
    }
    
    # Process in background
    background_tasks.add_task(
        process_batch_frames,
        job_id, frames, session_id, body_part, movement_type
    )
    
    return {"job_id": job_id, "status": "accepted"}

@router.get("/batch/status/{job_id}")
async def get_batch_status(job_id: str):
    """Get batch processing status"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]

async def process_batch_frames(
    job_id: str,
    frames: List[str],
    session_id: str,
    body_part: str,
    movement_type: str
):
    """Process frames in background"""
    analyzer = get_frame_analyzer()
    processing_jobs[job_id]["status"] = "processing"
    
    for i, frame_base64 in enumerate(frames):
        try:
            result = await analyzer.analyze(
                frame_base64=frame_base64,
                session_id=session_id,
                body_part=body_part,
                movement_type=movement_type,
                include_keypoints=True
            )
            
            processing_jobs[job_id]["results"].append(result)
            processing_jobs[job_id]["processed_frames"] = i + 1
            
        except Exception as e:
            processing_jobs[job_id]["results"].append({
                "error": str(e),
                "frame_index": i
            })
    
    processing_jobs[job_id]["status"] = "completed"