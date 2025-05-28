from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .chat.chat_router import router as chat_router
from .chat.websocket_router import router as websocket_router
from .graph.graph_router import router as graph_router

app = FastAPI(
    title="Nestle AI Chatbot",
    description="AI-based chatbot for the Made with Nestle website",
    version="1.0.0"
)

# Get environment variables for CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Configure CORS
if FRONTEND_URL.startswith("http://localhost") or FRONTEND_URL.startswith("http://127.0.0.1"):
    # Development CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production CORS    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            FRONTEND_URL, 
            FRONTEND_URL.replace("https://", "http://"), 
            FRONTEND_URL.replace("http://", "https://")
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    )

# Include routers
app.include_router(chat_router)
app.include_router(websocket_router)
app.include_router(graph_router)

@app.get("/")
async def root():
    return {
        "status": "healthy", 
        "message": "Nestle AI Chatbot API is running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 