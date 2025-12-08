#!/bin/bash
echo "Starting Backend..."
nohup python3 backend/app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

echo "Starting Frontend..."
python3 -m http.server 8000
