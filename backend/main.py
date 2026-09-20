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
from backend.routers import (
    auth,
    projects,
    context,
    versions,
    handoffs,
    admin,
    context_goals,
    context_decisions,
    context_tasks,
    context_technical_state,
)

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
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^chrome-extension://.*",
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
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(context_goals.router, prefix=settings.API_V1_PREFIX)
app.include_router(context_decisions.router, prefix=settings.API_V1_PREFIX)
app.include_router(context_tasks.router, prefix=settings.API_V1_PREFIX)
app.include_router(context_technical_state.router, prefix=settings.API_V1_PREFIX)

import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("continuo.backend")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception processing {request.method} {request.url.path}: {exc}")
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later."}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

@app.get("/", tags=["System"])
@app.head("/", tags=["System"])
def root():
    """Root endpoint for pingers, uptime checks, and service info."""
    return {
        "status": "operational",
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "health_check": "/health"
    }

@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
@app.head("/health", tags=["System"])
def health_check():
    """System health check and status."""
    return {
        "status": "operational",
        "platform": "Continuo Context Layer",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "engine": "active"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8008"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
