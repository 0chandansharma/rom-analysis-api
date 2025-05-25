# ROM Analysis API

A cloud-ready API for real-time Range of Motion (ROM) analysis using pose estimation. Built with FastAPI and RTMLib, it provides accurate joint angle calculations for physical therapy and fitness applications.

## Features

- **Real-time Pose Detection**: Using RTMLib with HALPE_26 model for accurate keypoint detection
- **Comprehensive ROM Analysis**: Currently supports lower back movements (flexion, extension, lateral flexion, rotation)
- **WebSocket Support**: Real-time streaming analysis for live assessments
- **Session Management**: Track ROM progress across multiple frames
- **Cloud-Ready**: Optimized for deployment with CPU/GPU support auto-detection
- **RESTful API**: Standard HTTP endpoints for frame-by-frame analysis

## Quick Start

### Prerequisites

- Python 3.9+
- pip or conda
- (Optional) CUDA-capable GPU for faster processing

### Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd rom-analysis-api
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` file:

```bash
cp .env.example .env
```

### Running the API

#### Local Development

```bash
# Direct run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the start script
python scripts/start_dev.py
```

#### Using Docker

```bash
# Build and run with docker-compose
docker-compose up

# Or build manually
docker build -t rom-analysis-api .
docker run -p 8000:8000 rom-analysis-api
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/api/v1/health/
```

### Analyze Single Frame

```python
import requests
import base64

# Encode your image
with open("image.jpg", "rb") as f:
    frame_base64 = base64.b64encode(f.read()).decode()

# Make request
response = requests.post(
    "http://localhost:8000/api/v1/analyze/analyze",
    json={
        "frame_base64": frame_base64,
        "session_id": "user123",
        "body_part": "lower_back",
        "movement_type": "flexion",
        "include_keypoints": True
    }
)

result = response.json()
print(f"Current angle: {result['rom']['current']}°")
print(f"Range: {result['rom']['min']}° to {result['rom']['max']}°")
```

### WebSocket Streaming

```javascript
// JavaScript/React example
const ws = new WebSocket("ws://localhost:8000/api/v1/ws/stream/user123");

// Send configuration
ws.onopen = () => {
  ws.send(
    JSON.stringify({
      body_part: "lower_back",
      movement_type: "flexion",
      include_keypoints: false,
    })
  );
};

// Handle responses
ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  if (result.status === "ready") {
    // Start sending frames
    sendVideoFrames();
  } else if (result.rom) {
    // Update UI with ROM data
    updateROMDisplay(result.rom);
  }
};

function sendVideoFrames() {
  // Get frame from video/webcam
  const canvas = captureFrame();
  canvas.toBlob((blob) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(",")[1];
      ws.send(base64);
    };
    reader.readAsDataURL(blob);
  }, "image/jpeg");
}
```

## API Endpoints

### REST Endpoints

| Method | Endpoint                                | Description          |
| ------ | --------------------------------------- | -------------------- |
| POST   | `/api/v1/analyze/analyze`               | Analyze single frame |
| GET    | `/api/v1/sessions/session/{session_id}` | Get session ROM data |
| DELETE | `/api/v1/sessions/session/{session_id}` | Clear session data   |
| GET    | `/api/v1/health/`                       | Health check         |
| GET    | `/api/v1/health/ready`                  | Readiness check      |

### WebSocket Endpoints

| Endpoint                         | Description                         |
| -------------------------------- | ----------------------------------- |
| `/api/v1/ws/{session_id}`        | Single frame analysis via WebSocket |
| `/api/v1/ws/stream/{session_id}` | Continuous streaming analysis       |

## Supported Movements

### Lower Back

- **Flexion**: Forward bending (0-60° normal range)
- **Extension**: Backward bending (-30-0° normal range)
- **Lateral Flexion**: Side bending (-30-30° normal range)
- **Rotation**: Twisting motion (-45-45° normal range)

### Coming Soon

- Shoulder (flexion, extension, abduction, adduction, rotation)
- Elbow (flexion, extension, pronation, supination)
- Hip (flexion, extension, abduction, adduction, rotation)
- Knee (flexion, extension)
- Ankle (dorsiflexion, plantarflexion, inversion, eversion)

## Response Format

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "frame_id": "session123_abc12345",
  "body_part": "lower_back",
  "movement_type": "flexion",
  "pose_detected": true,
  "angles": {
    "trunk": 45.2,
    "pelvis": 12.3,
    "right hip": 15.7,
    "left hip": 14.9
  },
  "rom": {
    "current": 45.2,
    "min": 5.1,
    "max": 45.2,
    "range": 40.1
  },
  "pose_confidence": 0.92,
  "validation": {
    "in_normal_range": true,
    "in_max_range": true,
    "message": "Angle is within normal range",
    "normal_range": [0, 60],
    "max_range": [0, 90]
  },
  "guidance": {
    "instruction": "Good position, continue the movement",
    "feedback": "Angle is within normal range",
    "improvement": "Maintain smooth, controlled motion"
  },
  "frame_metrics": {
    "keypoints_detected": 26,
    "angles_calculated": 4,
    "processing_time_ms": 45.3
  }
}
```

## Configuration

Key settings in `.env`:

```bash
# Model Configuration
POSE_MODEL="body_with_feet"  # or "body", "whole_body"
POSE_MODE="performance"       # or "lightweight", "balanced"
DEVICE="auto"                 # or "cpu", "cuda"

# Processing
CONFIDENCE_THRESHOLD=0.3
MIN_KEYPOINTS_RATIO=0.5
ANGLE_SMOOTHING_WINDOW=5

# Storage
USE_REDIS=false              # Set to true for production
REDIS_URL="redis://localhost:6379"
SESSION_TTL=3600
```

## Cloud Deployment

### AWS EC2 / Google Cloud

1. Use GPU-enabled instances for better performance (e.g., g4dn.xlarge)
2. Set `DEVICE=cuda` in environment
3. Use Redis for session storage in production

### Heroku / Railway

1. CPU-only deployment
2. Set `DEVICE=cpu` and `POSE_MODE=lightweight`
3. Consider using external Redis (e.g., Redis Cloud)

### Docker Deployment

```bash
# Production build
docker build -t rom-api:prod .
docker run -d \
  -p 8000:8000 \
  -e DEVICE=cpu \
  -e USE_REDIS=true \
  -e REDIS_URL=redis://redis:6379 \
  rom-api:prod
```

## Testing

Run the comprehensive test suite:

```bash
python scripts/test_endpoint.py
```

This will test:

- Health checks
- All movement types
- Session management
- WebSocket connections
- Streaming analysis

## Performance Tips

1. **Use GPU when available**: 3-5x faster processing
2. **Adjust detection frequency**: For stable subjects, reduce detection frequency
3. **Use lightweight mode**: For real-time applications with lower accuracy requirements
4. **Enable Redis**: For production deployments with multiple workers
5. **Batch processing**: Send multiple frames in one request when possible

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the BSD 3-Clause License.

## Acknowledgments

- RTMLib for pose detection models
- for angle calculation algorithms
- FastAPI for the excellent web framework

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug
