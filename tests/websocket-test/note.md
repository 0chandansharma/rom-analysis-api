cd rom-analysis-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Python 3

python -m http.server 8080

# Then open http://localhost:8080/test_websocket.html

localhost:8000

http://localhost:8080/tests/websocket-test/test_websocket.html

Option 1: Run the HTTP server from the correct directory
bash# Navigate to the root of your project (rom-analysis-api)
cd /path/to/rom-analysis-api

# Run the HTTP server

python -m http.server 8080

# Then access: http://localhost:8080/tests/websocket-test/test_websocket.html

Option 2: Run from the test directory
bash# Navigate to the websocket test directory
cd /path/to/rom-analysis-api/tests/websocket-test

# Run the HTTP server

python -m http.server 8080

# Then access: http://localhost:8080/test_websocket.html
