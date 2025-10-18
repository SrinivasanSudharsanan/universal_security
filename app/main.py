from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
import os
import logging

from app.config import Settings
from app.security.engine.security_engine import SecurityEngine
from app.api.endpoints import query, policies, audit, health
from app.database.init_db import init_db
from app.observability.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = Settings()

class PolylyticsApp:
    def __init__(self):
        self.app = FastAPI(
            title="Polylytics Universal Data Security Platform",
            description="Enterprise-grade security layer for universal data access",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        self.db_pool = None
        self.redis_client = None
        self.security_engine = None
        
    async def startup(self):
        """Initialize application state"""
        logger.info("Starting Polylytics Application")
        
        # Initialize database connection
        self.db_pool = await asyncpg.create_pool(settings.database_url)
        
        # Initialize Redis
        self.redis_client = redis.from_url(settings.redis_url)
        
        # Initialize security engine
        self.security_engine = SecurityEngine(self.db_pool, self.redis_client)
        
        # Initialize database schema
        await init_db(self.db_pool)
        
        logger.info("Polylytics Application started successfully")
    
    async def shutdown(self):
        """Cleanup application state"""
        logger.info("Shutting down Polylytics Application")
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()
    
    def setup_middleware(self):
        """Setup application middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup application routes"""
        self.app.include_router(query.router, prefix="/api/v1", tags=["query"])
        self.app.include_router(policies.router, prefix="/api/v1", tags=["policies"])
        self.app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
        self.app.include_router(health.router, prefix="/api/v1", tags=["health"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    polylytics_app = app.state.polylytics_app
    await polylytics_app.startup()
    yield
    await polylytics_app.shutdown()

# Create and configure the application
polylytics_app = PolylyticsApp()
polylytics_app.setup_middleware()
polylytics_app.setup_routes()

# Attach the app instance to FastAPI state
polylytics_app.app.state.polylytics_app = polylytics_app
polylytics_app.app.router.lifespan_context = lifespan

app = polylytics_app.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )