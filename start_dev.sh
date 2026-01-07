#!/bin/bash

# Trap to kill background processes on exit
trap "kill 0" EXIT

echo "Starting StockSim Development Environment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found. Please create one based on .env.example"
fi

# Start Backend
echo "Starting Backend (FastAPI)..."
./env/bin/uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (Next.js)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Wait for both
wait $BACKEND_PID $FRONTEND_PID
