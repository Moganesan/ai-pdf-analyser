#!/bin/bash

# AI PDF Analyzer - Ngrok Setup Script
# This script starts both the backend and frontend, then exposes the frontend via ngrok
# Next.js config automatically proxies API requests to backend

echo "🚀 Starting AI PDF Analyzer with Ngrok..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed. Please install it first:"
    echo "   brew install ngrok"
    echo "   or download from https://ngrok.com/"
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID $NGROK_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the backend
echo "📡 Starting backend server..."
cd backend
source bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start the frontend
echo "🌐 Starting frontend server..."
cd ..
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Start ngrok (exposing only the frontend)
echo "🌍 Starting ngrok tunnel..."
ngrok http 3000 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the ngrok URL
echo "🔗 Getting ngrok URL..."
sleep 2
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        if tunnel['proto'] == 'https':
            print(tunnel['public_url'])
            break
except:
    pass
")

if [ -n "$NGROK_URL" ]; then
    echo ""
    echo "✅ Setup complete!"
    echo "📱 Frontend URL (public): $NGROK_URL"
    echo "🔒 Backend URL (private): http://localhost:8000"
    echo ""
    echo "🌐 Open this URL to access your app: $NGROK_URL"
    echo "🔧 Backend API is private and only accessible from your machine"
    echo ""
    echo "Press Ctrl+C to stop all services"
else
    echo "❌ Failed to get ngrok URL. Check ngrok status at http://localhost:4040"
fi

# Wait for user to stop
wait
