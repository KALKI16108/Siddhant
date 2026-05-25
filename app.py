from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def serve_frontend_dashboard():
    """
    Serves the static 'index.html' file from the repository root as the frontend dashboard.
    """
    try:
        # Construct the absolute path to index.html
        # This assumes index.html is in the same directory as app.py
        # which is typically the repository root for simple deployments.
        file_path = os.path.join(os.path.dirname(__file__), "index.html")
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend Dashboard Not Found</h1><p>The 'index.html' file could not be found. Please ensure it is in the repository root directory.</p>",
            status_code=404
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error Loading Frontend Dashboard</h1><p>An unexpected error occurred: {e}</p>",
            status_code=500
        )

@app.get("/api/health")
async def health_check():
    """
    Returns a health check payload for API system monitoring.
    """
    return {
        "status": "healthy",
        "message": "Chabri Mahek Engine API is up and running!",
        "version": "1.0.0", # Example version
        "service": "chabri-mahek-engine-backend"
    }