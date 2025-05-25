from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from typing import Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test")
async def test_endpoint() -> Dict[str, Any]:
    """Simple test endpoint"""
    return {
        "message": "Test endpoint working",
        "data": {
            "test": True,
            "value": 123
        }
    }

@router.post("/test-echo")
async def test_echo(data: Dict[str, Any]) -> Dict[str, Any]:
    """Echo back the data received"""
    logger.info(f"Received data: {data}")
    return {
        "echo": data,
        "status": "received"
    }

@router.get("/websocket-test", response_class=HTMLResponse)
async def websocket_test_page():
    """Serve the WebSocket test page"""
    html_path = Path(__file__).parent.parent.parent.parent.parent / "scripts" / "websocket_test.html"
    
    if html_path.exists():
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        # Return embedded HTML if file not found
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WebSocket Test</title>
        </head>
        <body>
            <h1>WebSocket Test</h1>
            <p>HTML file not found at: {}</p>
        </body>
        </html>
        """.format(html_path))