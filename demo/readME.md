Setup and Run Instructions

Install dependencies:

bashcd demo/frontend
npm install

Start your ROM Analysis API:

bashcd ../../
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Start the demo app:

bashcd demo/frontend
npm run dev

Open in browser:
Navigate to http://localhost:3000
