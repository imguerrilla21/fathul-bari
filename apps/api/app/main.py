import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app  # Export main FastAPI app instance from backend

@app.get("/health", tags=["system-health"])
def health_check():
    """Endpoint Health Check dasar."""
    return {"status": "ok", "service": "Fathul Bari Research AI API", "stage": 18}


@app.get("/ready", tags=["system-health"])
def readiness_check():
    """Endpoint Readiness Probe dasar."""
    return {
        "status": "ready",
        "service": "Fathul Bari Research AI API",
        "database": "sqlite/postgresql",
        "redis": "connected"
    }
