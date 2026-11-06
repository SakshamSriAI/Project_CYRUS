"""CYRUS Main Application Entrypoint.

FastAPI application configuring routes, CORS middleware, lifespan events,
structured logging, and initial security headers.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.guardian import router as guardian_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.memory import router as memory_router
from backend.app.api.v1.research import router as research_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.voice import router as voice_router
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.lifecycle.process_manager import LifecycleState, process_manager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if settings.CYRUS_DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cyrus.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for FastAPI application."""
    logger.info("Initializing CYRUS Backend System...")
    # 1. Initialize SQLite Database with WAL mode
    db_info = await init_db()
    logger.info("Database initialized successfully at %s", db_info["db_path"])

    # 2. Transition lifecycle manager to ACTIVE state
    process_manager.set_state(LifecycleState.ACTIVE)
    logger.info("CYRUS is now in ACTIVE operational state.")

    yield

    # Shutdown sequence
    logger.info("CYRUS Backend is shutting down gracefully...")
    process_manager.set_state(LifecycleState.SHUTDOWN)
    logger.info("CYRUS Backend shutdown complete.")


app = FastAPI(
    title=settings.CYRUS_APP_NAME,
    version=settings.CYRUS_VERSION,
    description="Cybernetic Yet Responsive Unified System - Personal AI Operating System",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CYRUS_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API v1 Routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(guardian_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint welcoming the user to CYRUS."""
    return {
        "message": "CYRUS System Online",
        "owner": "Saksham",
        "version": settings.CYRUS_VERSION,
        "docs_url": "/docs",
        "health_url": "/api/v1/health",
        "chat_url": "/api/v1/chat/message",
    }
