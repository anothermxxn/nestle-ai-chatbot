import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """
    Represents a single message in a conversation.
    """
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }

@dataclass 
class ConversationSession:
    """
    Represents a conversation session with its history and metadata.
    """
    session_id: str
    messages: List[ConversationMessage]
    created_at: datetime
    last_activity: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a new message to the conversation."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.messages.append(message)
        self.last_activity = datetime.now()
        
    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get the most recent messages from the conversation."""
        return self.messages[-limit:] if limit > 0 else self.messages
        
    def get_conversation_context(self, max_messages: int = 8) -> List[ConversationMessage]:
        """Get conversation context for LLM prompts (limited number of recent messages)."""
        return self.get_recent_messages(max_messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format."""
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "metadata": self.metadata or {}
        }

class SessionManager:
    """
    In-memory session manager for conversation histories.
    Handles session creation, retrieval, and cleanup.
    """
    
    def __init__(self, session_timeout_hours: int = 24, max_sessions: int = 1000):
        """
        Initialize the session manager.
        
        Args:
            session_timeout_hours (int): Hours after which inactive sessions expire
            max_sessions (int): Maximum number of sessions to keep in memory
        """
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.max_sessions = max_sessions
        self._lock = Lock()
        
        logger.info(f"SessionManager initialized with {session_timeout_hours}h timeout, max {max_sessions} sessions")
    
    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            metadata (Optional[Dict[str, Any]]): Optional session metadata
            
        Returns:
            str: Session ID
        """
        with self._lock:
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            session = ConversationSession(
                session_id=session_id,
                messages=[],
                created_at=now,
                last_activity=now,
                metadata=metadata
            )
            
            self.sessions[session_id] = session
            
            # Clean up old sessions if we're at capacity
            self._cleanup_old_sessions()
            
            logger.info(f"Created new session: {session_id}")
            return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get a conversation session by ID.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Optional[ConversationSession]: Session if found, None otherwise
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                # Check if session has expired
                if datetime.now() - session.last_activity > self.session_timeout:
                    logger.info(f"Session {session_id} expired, removing")
                    del self.sessions[session_id]
                    return None
                
                return session
            
            return None
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to a conversation session.
        
        Args:
            session_id (str): Session ID
            role (str): Message role ("user" or "assistant")
            content (str): Message content
            metadata (Optional[Dict[str, Any]]): Optional message metadata
            
        Returns:
            bool: True if message was added successfully, False if session not found
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Attempted to add message to non-existent session: {session_id}")
            return False
        
        with self._lock:
            session.add_message(role, content, metadata)
            logger.debug(f"Added {role} message to session {session_id}")
            return True
    
    def get_conversation_history(self, session_id: str, max_messages: int = 20) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id (str): Session ID
            max_messages (int): Maximum number of recent messages to return
            
        Returns:
            List[Dict[str, Any]]: List of message dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        recent_messages = session.get_recent_messages(max_messages)
        return [msg.to_dict() for msg in recent_messages]
    
    def get_conversation_context(self, session_id: str) -> List[ConversationMessage]:
        """
        Get conversation context for LLM processing.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            List[ConversationMessage]: Recent messages for context
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.get_conversation_context()
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            bool: True if session was deleted, False if not found
        """
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current sessions.
        
        Returns:
            Dict[str, Any]: Session statistics
        """
        with self._lock:
            now = datetime.now()
            active_sessions = 0
            total_messages = 0
            
            for session in self.sessions.values():
                if now - session.last_activity <= self.session_timeout:
                    active_sessions += 1
                    total_messages += len(session.messages)
            
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "average_messages_per_session": total_messages / max(active_sessions, 1)
            }
    
    def _cleanup_old_sessions(self):
        """Clean up expired sessions and enforce session limits."""
        now = datetime.now()
        
        # Remove expired sessions
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if now - session.last_activity > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.debug(f"Cleaned up expired session: {session_id}")
        
        # If still over limit, remove oldest sessions
        if len(self.sessions) > self.max_sessions:
            # Sort by last activity and remove oldest
            sessions_by_activity = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_activity
            )
            
            sessions_to_remove = len(self.sessions) - self.max_sessions
            for i in range(sessions_to_remove):
                session_id, _ = sessions_by_activity[i]
                del self.sessions[session_id]
                logger.debug(f"Cleaned up old session due to limit: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Public method to manually trigger cleanup of expired sessions."""
        with self._lock:
            self._cleanup_old_sessions()
            logger.info("Manual session cleanup completed")

# Global session manager instance
session_manager = SessionManager() 