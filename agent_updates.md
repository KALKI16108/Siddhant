File Name: app.py
```python
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """
    Serves the front-end dashboard (index.html) from the repository root.
    """
    try:
        # Construct the path to index.html relative to the current file
        # For production, it's often safer to use __file__ and os.path.join
        # For this scenario, assuming index.html is in the same directory as app.py
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # Fallback if index.html is not found
        return HTMLResponse(
            content="<h1>Dashboard Not Found</h1><p>The <code>index.html</code> file could not be located.</p>",
            status_code=404
        )
    except Exception as e:
        # Generic error handling
        return HTMLResponse(
            content=f"<h1>Server Error</h1><p>An unexpected error occurred: {e}</p>",
            status_code=500
        )

@app.get("/api/health")
async def api_health_check():
    """
    Returns a health check payload for API system monitoring.
    """
    return {
        "status": "healthy",
        "service": "chabri-mahek-engine",
        "version": "1.0.0", # Example version
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# You can add other API endpoints below this line
# For example:
# @app.get("/api/items")
# async def get_items():
#     return {"items": ["item1", "item2"]}
```

File Name: render.yaml
```yaml
services:
  - type: web
    name: chabri-mahek-engine
    env: python
    buildCommand: pip install -r requirements.txt
    # The startCommand uses uvicorn to run the FastAPI application.
    # app:app refers to the 'app' variable within the 'app.py' module.
    # --host 0.0.0.0 makes the server accessible externally.
    # --port $PORT ensures it listens on the port provided by the hosting environment.
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      # DATABASE_URL is essential for connecting to a database.
      # sync: false means it's not automatically synced from a git repo
      # and should be manually configured in Render's environment variables.
      - key: DATABASE_URL
        sync: false
      # GEMINI_API_KEY for accessing external AI services.
      # Also marked as sync: false for security and environment-specific configuration.
      - key: GEMINI_API_KEY
        sync: false
```