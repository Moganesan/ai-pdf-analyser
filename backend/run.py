#!/usr/bin/env python3
"""
Backend server startup script
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Disable reload in production (Docker)
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        log_level="info"
    )
