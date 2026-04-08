"""
Sports AI — Main Application
FastAPI application with CORS, middleware, and startup events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.api.admin_routes import admin_router
from backend.agents.registry import discover_agents, all_agents
from backend.config.settings import get_settings
from backend.config.database import init_db
from backend.utils.cache import close_redis
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info("🚀 Sports AI starting up...")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   LLM Provider: {settings.llm_provider}")
    logger.info(f"   Max concurrent pipelines: {settings.max_concurrent_pipelines}")

    discover_agents()
    logger.info(f"   Registered agents: {len(all_agents())}")

    # Initialize database tables (dev only)
    if settings.is_development:
        try:
            await init_db()
            logger.info("   Database tables created")
        except Exception as e:
            logger.warning(f"   Database init skipped: {e}")

    logger.info("✓ Sports AI ready")

    yield

    # Shutdown
    logger.info("Shutting down Sports AI...")
    await close_redis()
    logger.info("Goodbye.")


app = FastAPI(
    title="Sports AI",
    description="Multi-agent predictive analysis system for sports betting",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(router)
app.include_router(admin_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.is_development,
    )
