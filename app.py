import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# Fallback health check endpoint
@app.get("/api/health")
def health_check():
    return {"status": "Live", "msg": "Mumbai Logistics Engine operational"}

# Serve the visual map dashboard directly on the root path
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    # If index.html exists, serve it; otherwise, provide a fallback interactive map frame
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
            
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIFlowix Logistics Terminal</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body { margin: 0; font-family: sans-serif; display: flex; height: 100vh; }
            #sidebar { width: 35%; padding: 20px; background: #f8f9fa; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }
            #map { width: 65%; height: 100%; }
            .btn { background: #007bff; color: white; padding: 10px; border: none; width: 100%; cursor: pointer; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h2>🚚 AIFlowix Engine</h2>
            <p><strong>Status:</strong> Live in Production</p>
            <hr/>
            <button class="btn" onclick="alert('System operating smoothly! Double-click map to test placement.')">Calculate & Dispatch</button>
        </div>
        <div id="map"></div>
        <script>
            var map = L.map('map').setView([19.0760, 72.8777], 12);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
            L.marker([19.0760, 72.8777]).addTo(map).bindPopup('Mumbai Hub Center').openPopup();
        </script>
    </body>
    </html>
    """
