from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

try:
    from backend.src.chat.chat_router import router as chat_router
    from backend.src.graph.graph_router import router as graph_router
except ImportError:
    from src.chat.chat_router import router as chat_router
    from src.graph.graph_router import router as graph_router

app = FastAPI(
    title="Nestle AI Chatbot",
    description="AI-based chatbot for the Made with Nestle website",
    version="1.0.0"
)

ENVIRONMENT = os.getenv("ENVIRONMENT")
DEV_FRONTEND_URL = os.getenv("DEV_FRONTEND_URL")
PROD_FRONTEND_URL = os.getenv("PROD_FRONTEND_URL")

if ENVIRONMENT == "production" and PROD_FRONTEND_URL:
    # Production CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[PROD_FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    )
else:
    # Development CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[DEV_FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(chat_router)
app.include_router(graph_router)

@app.get("/")
async def root():
    """
    Root endpoint that returns API status and environment information.

    Returns:
        dict: Status, message, and environment information
    """
    return {
        "status": "healthy", 
        "message": "Nestle AI Chatbot API is running",
        "environment": ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring API availability.

    Returns:
        dict: Status and environment information
    """
    return {"status": "healthy", "environment": ENVIRONMENT} 