"""
Main FastAPI Application.

This is the entry point for the application. It:
1. Creates the FastAPI app with lifespan management
2. Configures middleware (CORS, etc.)
3. Mounts all routers
4. Provides the uvicorn run command
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from churn_agent.api.router import router as analysis_router
from churn_agent.api.dependencies import init_redis_pool, close_redis_pool
from churn_agent.core.config import get_settings
from churn_agent.core.logging import setup_logging, get_logger

# Initialize logging first
setup_logging()
logger = get_logger(__name__)



# Lifespan Management


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Initialize/close Redis connection pool
    - Initialize/close database connections
    - Start/stop background workers
    """
    settings = get_settings()
    
    # ─── Startup ───
    logger.info(
        "Starting application",
        app_name=settings.app_name,
        environment=settings.environment,
        debug=settings.debug,
    )
    
    # Initialize Redis
    await init_redis_pool(settings)
    
    # TODO: Initialize database connection pool
    # await init_db_pool(settings)
    
    logger.info("Application startup complete")
    
    yield  # Application runs here
    
    #  Shutdown Application
    logger.info("Shutting down application")
    
    # Close Redis
    await close_redis_pool()
    
    # TODO: Close database connections
    # await close_db_pool()
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory function.
    
    Creates and configures the FastAPI application.
    Useful for testing with different configurations.
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="Autonomous Churn Prediction Agent powered by CrewAI",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )
    
    # ─── Middleware ───
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    
    # ─── Exception Handlers ───
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all exception handler for unexpected errors."""
        logger.exception(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
        
        # Don't expose internal errors in production
        detail = str(exc) if settings.is_development else "Internal server error"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_error",
                "detail": detail,
            },
        )
    
    # ─── Routers ───
    
    # Root health check
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """Root endpoint - basic health check."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "ok",
        }
    
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        """Kubernetes/Docker health check endpoint."""
        return {"status": "healthy"}
    
    # Mount API routers
    app.include_router(
        analysis_router,
        prefix=settings.api_prefix,
    )
    
    return app


app = create_app()



# CLI Entry Point


def run() -> None:
    """
    Run the application with uvicorn.
    
    Called via: `churn-agent` (from pyproject.toml scripts)
    Or directly: `python -m churn_agent.main`
    """
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "churn_agent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=settings.is_development,
    )


if __name__ == "__main__":
    run()