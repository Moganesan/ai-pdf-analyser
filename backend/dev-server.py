#!/usr/bin/env python3
"""
Development server with hot reload for AI PDF Analyzer Backend
"""
import uvicorn
import os
import sys

def main():
    # Ensure we're in the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Add the backend directory to Python path
    sys.path.insert(0, backend_dir)
    
    print("🚀 Starting AI PDF Analyzer Backend with hot reload...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[0]}")
    print("🔄 Hot reload enabled - server will restart on file changes")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Start the server with hot reload
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app", "."],
        reload_includes=["*.py", "*.json"],
        reload_excludes=["*.pyc", "__pycache__", "chroma_db", "uploads"],
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
