#!/usr/bin/env python3
"""
Server startup helper to avoid import issues
"""
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Start server
import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting FastAPI server on localhost:8002")
    print("📱 Access at: http://localhost:8002/professional")
    print("🛑 Press Ctrl+C to stop")

    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True, log_level="info")
