from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
from datetime import datetime

try:
    from backend.src.chat.services import NestleChatClient, session_manager
except ImportError:
    from src.chat.services import NestleChatClient, session_manager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])

# Global chat client instance
chat_client = None

def get_chat_client():
    """Get or create chat client instance."""
    global chat_client
    if chat_client is None:
        chat_client = NestleChatClient()
    return chat_client

def handle_chat_error(error: Exception, context: str):
    """Handle chat API errors consistently."""
    logger.error(f"Error in {context}: {str(error)}")
    raise HTTPException(status_code=500, detail=f"Internal server error: {str(error)}")

# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat queries with session management."""
    query: str = Field(..., description="User's question or search query", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for conversation history (if None, new session created)")
    content_type: Optional[str] = Field(None, description="Filter by content type (e.g., 'recipe', 'brand')")
    brand: Optional[str] = Field(None, description="Filter by brand (e.g., 'NESTEA')")
    keywords: Optional[List[str]] = Field(None, description="Filter by keywords")
    top_search_results: int = Field(5, description="Number of search results to use", ge=1, le=20)

class ChatResponse(BaseModel):
    """Response model for chat queries."""
    answer: str = Field(..., description="Generated answer from the AI assistant")
    sources: List[Dict] = Field(..., description="Source documents used for the answer")
    search_results_count: int = Field(..., description="Number of search results used")
    query: str = Field(..., description="Original query")
    session_id: str = Field(..., description="Session ID for this conversation")
    filters_applied: Dict = Field(..., description="Filters that were applied")
    graphrag_enhanced: bool = Field(..., description="Whether GraphRAG was successfully used for enhanced context")
    combined_relevance_score: Optional[float] = Field(0.0, description="Combined relevance score from GraphRAG")
    retrieval_metadata: Optional[Dict] = Field({}, description="Metadata about the retrieval process")

class SessionRequest(BaseModel):
    """Request model for creating a new session."""
    metadata: Optional[Dict] = Field(None, description="Optional session metadata")

class SessionResponse(BaseModel):
    """Response model for session operations."""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="Operation result message")

class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    session_id: str = Field(..., description="Session ID")
    messages: List[Dict] = Field(..., description="Conversation messages")
    total_messages: int = Field(..., description="Total number of messages in conversation")

@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest = SessionRequest()):
    """
    Create a new conversation session.
    
    Returns a session ID that should be used for subsequent chat requests
    to maintain conversation context.
    """
    try:
        session_id = session_manager.create_session(metadata=request.metadata)
        
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )
        
    except Exception as e:
        handle_chat_error(e, "create_session")

@router.get("/sessions/{session_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    limit: int = Query(20, description="Maximum number of recent messages", ge=1, le=100)
):
    """
    Get conversation history for a session.
    """
    try:
        messages = session_manager.get_conversation_history(session_id, limit)
        
        if not session_manager.get_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=messages,
            total_messages=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_chat_error(e, "get_conversation_history")

@router.delete("/sessions/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str):
    """
    Delete a conversation session and its history.
    """
    try:
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session_id,
            message="Session deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        handle_chat_error(e, "delete_session")

@router.get("/sessions/stats")
async def get_session_stats():
    """
    Get statistics about current sessions.
    """
    try:
        stats = session_manager.get_session_stats()
        return {
            "session_statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        handle_chat_error(e, "get_session_stats")

@router.post("/search", response_model=ChatResponse)
async def chat_search(request: ChatRequest):
    """
    Perform a conversational search and get an AI-generated answer.
    
    This endpoint uses session-based conversation management:
    1. If no session_id provided, creates a new session
    2. Adds user message to session history
    3. Retrieves conversation context from session
    4. Performs RAG search and generates response
    5. Adds assistant response to session history
    
    The session ID should be used for subsequent requests to maintain context.
    """
    try:
        client = get_chat_client()
        
        # Create or get session
        if not request.session_id:
            session_id = session_manager.create_session()
            logger.info(f"Created new session for chat: {session_id}")
        else:
            session_id = request.session_id
            if not session_manager.get_session(session_id):
                raise HTTPException(status_code=404, detail="Session not found")
        
        # Add user message to session
        session_manager.add_message(session_id, "user", request.query)
        
        # Get conversation context from session
        conversation_context = session_manager.get_conversation_context(session_id)
        
        # Perform search and chat
        response = await client.search_and_chat(
            query=request.query,
            conversation_history=conversation_context,
            content_type=request.content_type,
            brand=request.brand,
            keywords=request.keywords,
            top_search_results=request.top_search_results
        )
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
        
        # Add assistant response to session
        session_manager.add_message(session_id, "assistant", response["answer"])
        
        # Add session_id to response
        response["session_id"] = session_id
        
        return ChatResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        handle_chat_error(e, "chat_search")

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    try:
        get_chat_client()  # Verify client can be created
        session_stats = session_manager.get_session_stats()
        
        return {
            "status": "healthy",
            "service": "Nestle Chat API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "azure_openai": "connected",
                "azure_search": "connected",
                "session_manager": "active"
            },
            "session_stats": session_stats
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "Nestle Chat API", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }