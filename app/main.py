from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ResilioAI Test API",
    description="API Pengujian Deployment Backend ResilioAI untuk GTNIC 2026",
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
# kakka
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