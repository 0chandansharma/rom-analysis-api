#!/bin/bash

# Test if the server is running
echo "Testing if server is running..."
curl -s http://localhost:8000/api/v1/health/ | jq .

echo -e "\n\nTesting WebSocket with websocat (install with: brew install websocat)"
echo "If websocat is not installed, you can use the Python test scripts instead"

# Simple WebSocket test using websocat
if command -v websocat &> /dev/null; then
    echo -e "\nTesting WebSocket connection..."
    
    # Create a test message
    TEST_MESSAGE='{
        "frame_base64": "test_frame_data",
        "body_part": "lower_back",
        "movement_type": "flexion",
        "include_keypoints": false
    }'
    
    echo "Sending test message to WebSocket..."
    echo "$TEST_MESSAGE" | websocat -n1 ws://localhost:8000/ws/test_session_curl
else
    echo "websocat not found. Use Python test scripts or install websocat."
fi

echo -e "\n\nYou can also test WebSocket using:"
echo "1. python scripts/test_websocket_live.py"
echo "2. Open tests/websocket-test/test_websocket.html in a browser"
echo "3. Use the Python test script in tests/websocket-test/test.py"