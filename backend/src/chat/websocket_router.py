from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging
import asyncio
import time

from .chat_client import NestleChatClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_connections: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, conversation_id: str = None):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if conversation_id:
            if conversation_id not in self.conversation_connections:
                self.conversation_connections[conversation_id] = []
            self.conversation_connections[conversation_id].append(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (conversation: {conversation_id})")
    
    def disconnect(self, connection_id: str, conversation_id: str = None):
        """Disconnect a WebSocket client."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if conversation_id and conversation_id in self.conversation_connections:
            if connection_id in self.conversation_connections[conversation_id]:
                self.conversation_connections[conversation_id].remove(connection_id)
            
            # Clean up empty conversation lists
            if not self.conversation_connections[conversation_id]:
                del self.conversation_connections[conversation_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                # Remove broken connection
                self.disconnect(connection_id)
    
    async def broadcast_to_conversation(self, message: dict, conversation_id: str):
        """Broadcast a message to all connections in a conversation."""
        if conversation_id in self.conversation_connections:
            for connection_id in self.conversation_connections[conversation_id].copy():
                await self.send_personal_message(message, connection_id)

# Global connection manager
manager = ConnectionManager()

# Global chat client
chat_client = None

def get_chat_client():
    """Get or create chat client instance."""
    global chat_client
    if chat_client is None:
        chat_client = NestleChatClient()
    return chat_client

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat communication.
    
    Handles basic chat functionality without conversation grouping.
    """
    connection_id = f"conn_{int(time.time() * 1000)}"
    
    await manager.connect(websocket, connection_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "system",
            "message": "Connected to Nestle AI Chatbot",
            "connection_id": connection_id
        }, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                await handle_websocket_message(message_data, connection_id)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, connection_id)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, connection_id)
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)

@router.websocket("/ws/{conversation_id}")
async def websocket_conversation_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for conversation-specific chat communication.
    
    Handles chat functionality with conversation grouping and broadcasting.
    """
    connection_id = f"conv_{conversation_id}_{int(time.time() * 1000)}"
    
    await manager.connect(websocket, connection_id, conversation_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "system",
            "message": f"Connected to conversation: {conversation_id}",
            "connection_id": connection_id,
            "conversation_id": conversation_id
        }, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_data["conversation_id"] = conversation_id
                await handle_websocket_message(message_data, connection_id, conversation_id)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, connection_id)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error"
                }, connection_id)
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id, conversation_id)

async def handle_websocket_message(message_data: dict, connection_id: str, conversation_id: str = None):
    """
    Handle incoming WebSocket messages and route them appropriately.
    
    Args:
        message_data: The parsed message data
        connection_id: The connection identifier
        conversation_id: Optional conversation identifier
    """
    message_type = message_data.get("type", "chat")
    
    if message_type == "chat":
        await handle_chat_message(message_data, connection_id, conversation_id)
    elif message_type == "ping":
        await handle_ping_message(connection_id, conversation_id)
    elif message_type == "typing":
        await handle_typing_message(message_data, connection_id, conversation_id)
    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, connection_id)

async def handle_chat_message(message_data: dict, connection_id: str, conversation_id: str = None):
    """Handle chat messages and generate AI responses."""
    user_message = message_data.get("message", "").strip()
    
    if not user_message:
        await manager.send_personal_message({
            "type": "error",
            "message": "Empty message received"
        }, connection_id)
        return
    
    # Send typing indicator
    typing_message = {
        "type": "typing",
        "is_typing": True,
        "sender": "assistant"
    }
    
    if conversation_id:
        await manager.broadcast_to_conversation(typing_message, conversation_id)
    else:
        await manager.send_personal_message(typing_message, connection_id)
    
    try:
        # Get AI response
        client = get_chat_client()
        response = await client.search_and_chat(
            query=user_message,
            top_search_results=5
        )
        
        if "error" in response:
            raise Exception(response["error"])
        
        # Send response
        response_message = {
            "type": "chat_response",
            "message": response.get("answer", "I'm sorry, I couldn't generate a response."),
            "references": response.get("sources", []),
            "sender": "assistant",
            "timestamp": time.time()
        }
        
        if conversation_id:
            response_message["conversation_id"] = conversation_id
            await manager.broadcast_to_conversation(response_message, conversation_id)
        else:
            await manager.send_personal_message(response_message, connection_id)
    
    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        error_message = {
            "type": "error",
            "message": "Sorry, I encountered an error processing your message."
        }
        
        if conversation_id:
            await manager.broadcast_to_conversation(error_message, conversation_id)
        else:
            await manager.send_personal_message(error_message, connection_id)
    
    finally:
        # Stop typing indicator
        stop_typing_message = {
            "type": "typing",
            "is_typing": False,
            "sender": "assistant"
        }
        
        if conversation_id:
            await manager.broadcast_to_conversation(stop_typing_message, conversation_id)
        else:
            await manager.send_personal_message(stop_typing_message, connection_id)

async def handle_ping_message(connection_id: str, conversation_id: str = None):
    """Handle ping messages for connection health checks."""
    pong_message = {
        "type": "pong",
        "timestamp": time.time()
    }
    
    if conversation_id:
        pong_message["conversation_id"] = conversation_id
    
    await manager.send_personal_message(pong_message, connection_id)

async def handle_typing_message(message_data: dict, connection_id: str, conversation_id: str = None):
    """Handle typing indicator messages."""
    if conversation_id:
        # Broadcast typing status to other users in the conversation
        typing_message = {
            "type": "typing",
            "is_typing": message_data.get("is_typing", False),
            "sender": "user",
            "connection_id": connection_id
        }
        
        # Don't send back to the sender
        for other_connection_id in manager.conversation_connections.get(conversation_id, []):
            if other_connection_id != connection_id:
                await manager.send_personal_message(typing_message, other_connection_id) 