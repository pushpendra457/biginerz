# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from ml_models import model_registry

from app.config import get_settings
from app.database import connect_db, disconnect_db
from app.resources import auth_resources, rep_resources # Import your new resources router

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings from config.py
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Replaces the old @app.on_event("startup") decorators.
    """
    logger.info("Starting up: Initializing database connection pool...")
    await connect_db()
    model_registry.preload_all()
    
    yield  # Application is running and serving requests
    
    logger.info("Shutting down: Closing database connections...")
    await disconnect_db()

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# ── Middlewares ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to measure response time for every API call."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        # Fallback for unhandled exceptions to prevent server crash loops
        logger.error(f"Unhandled error: {e}")
        return JSONResponse(
            status_code=500, 
            content={"detail": "Internal Server Error"}
        )
        
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# ── Routers ──────────────────────────────────────────────────
# Mount the API resources (endpoints)

app.include_router(auth_resources.router, prefix="/api/v1")
app.include_router(rep_resources.router, prefix="/api/v1")

# ── Health Check ─────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Simple ping endpoint to verify the server is running."""
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "models": model_registry.health()
    }

