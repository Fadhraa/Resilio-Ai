from dotenv import load_dotenv

# Muat variabel konfigurasi dari file .env
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.v1.router import api_router

app = FastAPI(
    title="ResilioAI Engine API",
    description="Hybrid Multi-Agent & Deterministic Pipeline for Supply Chain Resilience - SPPG GTNIC 2026",
    version="1.0.0"
)

# Konfigurasi CORS agar frontend (Next.js/Vercel) bisa memanggil API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Membuka akses untuk semua domain saat pengujian
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hubungkan API Router v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "Backend ResilioAI berhasil dideploy dan berjalan di Render!",
        "service": "FastAPI Multi-Agent Engine"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected (mock)",
        "agent_status": "ready"
    }
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)