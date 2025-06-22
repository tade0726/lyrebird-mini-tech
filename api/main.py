from fastapi import FastAPI

from api.config import settings
from api.utils.logging import get_logger, setup_logging
from api.auth import router as auth_router
from api.dictations import router as dictations_router

# Set up logging configuration
setup_logging()

# Set up logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

# Include routers
app.include_router(auth_router)
app.include_router(dictations_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    logger.debug("Root endpoint called")
    return {"message": "Welcome to Lyrebird API!"}
