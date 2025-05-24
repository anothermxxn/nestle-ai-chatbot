from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .chat.chat_router import router as chat_router

app = FastAPI(
    title="Nestle AI Chatbot",
    description="AI-based chatbot for the Made with Nestle website",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Update this with actual frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)

@app.get("/")
async def root():
    return {
        "status": "healthy", 
        "message": "Nestle AI Chatbot API is running"
    } 