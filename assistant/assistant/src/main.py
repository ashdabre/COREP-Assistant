# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# import logging

# from src.config.settings import settings
# from src.api.endpoints import router
# from src.data.database import init_db, close_db
# from src.regulatory_data.embeddings import init_embeddings

# logging.basicConfig(level=settings.LOG_LEVEL)
# logger = logging.getLogger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     logger.info("Initializing application...")
#     await init_db()
#     await init_embeddings()
#     logger.info("Application initialized")
#     yield
#     # Shutdown
#     await close_db()
#     logger.info("Application shutdown")

# app = FastAPI(
#     title="COREP Regulatory Reporting Assistant",
#     description="LLM-assisted PRA COREP reporting assistant prototype",
#     version="1.0.0",
#     lifespan=lifespan
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(router, prefix="/api/v1")

# @app.get("/")
# async def root():
#     return {
#         "message": "COREP Regulatory Reporting Assistant API",
#         "version": "1.0.0",
#         "available_templates": ["C_01.00", "C_02.00"]
#     }

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "service": "corep-assistant"}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="COREP Regulatory Reporting Assistant",
    description="LLM-assisted PRA COREP reporting assistant prototype",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting COREP Regulatory Assistant...")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Initialize database
    try:
        from src.data.database import init_db
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

@app.get("/")
async def root():
    return {
        "message": "COREP Regulatory Reporting Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        },
        "endpoints": {
            "health": "/health",
            "templates": "/api/v1/templates",
            "generate_report": "/api/v1/report (POST)",
            "search_regulations": "/api/v1/regulations/search"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        from src.data.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "corep-assistant",
            "components": {
                "database": "operational",
                "api": "operational"
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "corep-assistant",
            "error": str(e),
            "components": {
                "database": "unavailable",
                "api": "operational"
            }
        }

# Import and include API routes
try:
    from src.api.endpoints import router
    app.include_router(router, prefix="/api/v1")
    logger.info("API endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"API endpoints module not found: {e}")
    
    # Create basic endpoints
    from fastapi import APIRouter
    from pydantic import BaseModel
    from typing import Optional
    
    basic_router = APIRouter()
    
    class BasicRequest(BaseModel):
        question: str
        scenario: Optional[str] = None
        template_id: str = "C_01.00"
    
    @basic_router.post("/report")
    async def generate_report(request: BasicRequest):
        return {
            "session_id": "demo-session-123",
            "template_id": request.template_id,
            "populated_fields": {
                "C_01.00_r010_c010": {
                    "value": "1500000.00",
                    "confidence": 0.95,
                    "reasoning": "Based on regulatory text PRA_RB_4.2.1"
                }
            },
            "message": "This is a demo response. Set up Grok API key for real processing."
        }
    
    @basic_router.get("/templates")
    async def list_templates():
        return {
            "templates": [
                {"id": "C_01.00", "name": "Own Funds", "description": "Own funds calculation"},
                {"id": "C_02.00", "name": "Capital Requirements", "description": "Capital requirements reporting"}
            ]
        }
    
    app.include_router(basic_router, prefix="/api/v1")
except Exception as e:
    logger.error(f"Failed to setup API routes: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")