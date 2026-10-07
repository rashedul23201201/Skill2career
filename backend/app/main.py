from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, setup_logging
from app.core.exceptions import register_exception_handlers
from app.routers.api_router import api_router

# Setup application logging
setup_logging()

# Instantiate FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Bangladesh Job Preparation Ecosystem API - Learn Today, Get Hired Tomorrow",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Register CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?:\/\/(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

# Register centralized exception handlers
register_exception_handlers(app)

# Register modular routers with API v1 versioning via master api_router
app.include_router(api_router, prefix=settings.API_V1_STR)



@app.get("/", tags=["Root"])
def root():
    """Root endpoint providing service metadata."""
    return {
        "service": settings.APP_NAME,
        "tagline": "Learn Today, Get Hired Tomorrow",
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
