from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from .routers import auth, images, live, dashboard
from .config import UPLOAD_DIR
from .database import init_db

app = FastAPI(
    title="AI Based Fabric Defects Detection System API",
    description="API for AI-based fabric defect detection with image upload and live stream",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(images.router)
app.include_router(live.router)
app.include_router(dashboard.router)


@app.get("/uploads/{filename}")
async def get_upload(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}, 404


@app.get("/")
def root():
    return {"message": "Fabric Defect Detection API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
