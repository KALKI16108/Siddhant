import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
import psycopg2

app = FastAPI(title="AIFlowix Logistics API")

# Cross-Origin Resource Sharing (CORS) allow karo taaki frontend connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase Database Connection Setup
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    # Database connect karne ka helper function
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

@app.get("/")
def home():
    return {"status": "online", "message": "AIFlowix Mumbai Logistics Core Engine Ready"}

@app.get("/api/test-db")
def test_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        db_time = cur.fetchone()
        cur.close()
        conn.close()
        return {"database": "connected", "server_time": db_time}
    except Exception as e:
        return {"database": "error", "details": str(e)}
      # Placeholder file for the main application entry point or core logic.
# This file would typically house the main application bootstrap or server-side logic.
