"""
CONTINUO — Universal Context Platform Backend API
FastAPI Application Entrypoint
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.routers import auth, projects, context, versions, handoffs

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-agnostic context and project memory layer that lets you continue your work across AI platforms.",
    lifespan=lifespan
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev and Chrome extension
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(projects.router, prefix=settings.API_V1_PREFIX)
app.include_router(context.router, prefix=settings.API_V1_PREFIX)
app.include_router(versions.router, prefix=settings.API_V1_PREFIX)
app.include_router(handoffs.router, prefix=settings.API_V1_PREFIX)

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """System health check and status."""
    return {
        "status": "operational",
        "platform": "Continuo Context Layer",
        "version": settings.VERSION,
        "engine": "active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
