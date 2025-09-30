from fastapi import FastAPI
import logging,os,uvicorn
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from contextlib import asynccontextmanager
from app.config.settings import settings
from app.config.db_connection import async_engine,Base
from app.api import api_router
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: runs on startup and shutdown."""
    # ✅ Startup
    logger.info("Starting up Smart Home Interior API...")
    logger.info(f"📁 Upload directory: {settings.upload_dir}")
    # Create upload dir 
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Mount static files for file serving
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    # Test DB connection
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            
            # ✅ Conditionally create tables in development mode
            if settings.debug:
                # ✅ Create ENUM type first
                # await conn.run_sync(contact_status_enum.create, checkfirst=True)
                
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Tables created (development mode)")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

    logger.info("Smart Home Interior API started successfully")
    yield  # <-- App runs and serves requests here

    # ✅ Shutdown
    logger.info("Shutting down Smart Home Interior API...")
    await async_engine.dispose()
    logger.info("Database connections closed")
    logger.info("Smart Home Interior API shutdown complete")  

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description="Smart Home Interior API",
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
              )

# Include Routers
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        reload=settings.debug,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )