#!/bin/bash
# ADSA Compression System - Setup and Run Script

echo "=========================================="
echo "  ADSA File Compression System"
echo "  Frontend & Backend Setup"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo "✅ Python dependencies installed"

# Start the Flask backend
echo ""
echo "🚀 Starting Flask backend server..."
echo "   Backend will run on: http://localhost:5000"
python3 app.py &
BACKEND_PID=$!

sleep 2

# Display frontend info
echo ""
echo "=========================================="
echo "✅ Backend Started!"
echo ""
echo "🌐 Frontend Information:"
echo "   Open this file in your browser:"
echo "   file://$(pwd)/index.html"
echo ""
echo "   Or use a local web server (recommended):"
echo "   python3 -m http.server 8000"
echo "   Then open: http://localhost:8000/index.html"
echo ""
echo "📚 API Endpoints:"
echo "   GET  /api/health                 - Health check"
echo "   GET  /api/algorithms             - List algorithms"
echo "   POST /api/compress               - Compress file"
echo "   POST /api/decompress             - Decompress file"
echo "   POST /api/analyze                - Analyze file"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="

wait $BACKEND_PID
