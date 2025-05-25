cd rom-analysis-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Python 3

python -m http.server 8080

# Then open http://localhost:8080/test_websocket.html
