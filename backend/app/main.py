"""
FastAPI Main Application
OIL Q&A Search Tool Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.core.config import settings
from app.core.database import db

# Create FastAPI app
app = FastAPI(
    title="OIL Q&A Search API",
    description="AI-powered Q&A search and generation for Online Income Lab",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting OIL Q&A API...")
    print(f"📊 Environment: {settings.environment}")
    print(f"🤖 Default provider: {settings.default_model_provider}")

    # Connect to database
    try:
        db.connect()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection error: {e}")

    print("✨ API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down OIL Q&A API...")
    db.disconnect()
    print("✅ Cleanup complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "OIL Q&A Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
