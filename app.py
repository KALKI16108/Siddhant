from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def read_root():
    return HTMLResponse("<h1>AIFlowix Live Terminal Ready</h1>")

@app.get("/api/health")
def health():
    return {"status": "Live"}
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
