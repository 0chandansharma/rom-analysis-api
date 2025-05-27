# app/api/v1/endpoints/stream.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
import time

router = APIRouter()

@router.post("/stream/analyze")
async def stream_analysis(request: Request):
    """Server-Sent Events endpoint for streaming analysis"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        # Parse initial request body
        body = await request.json()
        session_id = body.get("session_id")
        body_part = body.get("body_part")
        movement_type = body.get("movement_type")
        
        # Get analyzer instance
        analyzer = get_frame_analyzer()
        
        try:
            while True:
                # Check if client is still connected
                if await request.is_disconnected():
                    break
                
                # In production, you'd get frames from a queue
                # For now, this is a placeholder
                yield f"data: {json.dumps({'status': 'waiting_for_frame'})}\n\n"
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            # Clean up
            pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )