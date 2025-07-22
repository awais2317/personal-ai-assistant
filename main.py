import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from config.settings import settings
from api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Personal AI Assistant",
    description="A comprehensive AI assistant for document analysis, business planning, and personal organization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path("static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["AI Assistant"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve the chat interface page"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Serve the document upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/business", response_class=HTMLResponse)
async def business_page(request: Request):
    """Serve the business analysis page"""
    return templates.TemplateResponse("business.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Personal AI Assistant...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Upload folder: {settings.UPLOAD_FOLDER}")
    logger.info(f"Vector DB path: {settings.CHROMA_DB_PATH}")
    
    # Verify OpenAI API key
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
        logger.warning("OpenAI API key not configured! Please set OPENAI_API_KEY in .env file")
    else:
        logger.info("OpenAI API key configured")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Personal AI Assistant...")

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
