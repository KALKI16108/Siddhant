from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def read_root():
    html_content = "<h1>AIFlowix Live Terminal Ready</h1><p>Status: Live in Production</p>"
    return HTMLResponse(content=html_content)

@app.get("/api/health")
def health():
    return {"status": "Live"}
