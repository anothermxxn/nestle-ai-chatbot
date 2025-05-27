#!/bin/bash

# Nestle AI Chatbot Startup Script
# This script starts both the backend and frontend servers

echo "Starting Nestle AI Chatbot..."
echo "================================"

cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if virtual environment exists for backend
if [ ! -d "../backend/venv" ]; then
    echo "❌ Backend virtual environment not found at backend/venv"
    echo "Please create a virtual environment first:"
    echo "  cd ../backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if node_modules exists for frontend
if [ ! -d "../frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed"
    echo "Please install frontend dependencies first:"
    echo "  cd ../frontend && npm install"
fi

echo "Starting Backend Server..."
echo "------------------------------"
cd ../backend
source venv/bin/activate
# Set PYTHONPATH to include the project root so backend.config imports work
export PYTHONPATH="$(pwd)/..:$PYTHONPATH"
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 3

echo ""
echo "Starting Frontend Server..."
echo "------------------------------"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers are starting up!"
echo "================================"
echo "Backend API: http://localhost:8000"
echo "Frontend App: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "================================"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 