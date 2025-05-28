import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .context_manager import ChatMessage, SearchContext, ContextExtractor
from config import CHAT_CONFIG

logger = logging.getLogger(__name__)

class ConversationSession:
    """Manages a single conversation session with context."""
    
    def __init__(self, session_id: str = None, max_history: int = None, context_window: int = None):
        """
        Initialize a conversation session.
        
        Args:
            session_id (str): Unique session identifier
            max_history (int): Maximum number of messages to keep in history
            context_window (int): Number of recent messages to use for context
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.max_history = max_history or CHAT_CONFIG["max_conversation_history"]
        self.context_window = context_window or CHAT_CONFIG["context_window"]
        
        # Message history
        self.messages: List[ChatMessage] = []
        
        # Search context
        self.search_context = SearchContext(
            recent_topics=[],
            preferred_content_types=[],
            mentioned_brands=[],
            mentioned_products=[],
            conversation_themes=[]
        )
        
        # Session metadata
        self.metadata = {
            "total_queries": 0,
            "total_responses": 0,
            "preferred_language": "en",
            "user_preferences": {}
        }
        
        # Context extractor for analyzing user input
        self.context_extractor = ContextExtractor()
    
    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a user message to the conversation."""
        message = ChatMessage(
            role="user",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self._add_message(message)
        self.metadata["total_queries"] += 1
        
        # Extract context information from user input
        self.context_extractor.update_search_context(content, self.search_context)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add an assistant message to the conversation."""
        message = ChatMessage(
            role="assistant",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self._add_message(message)
        self.metadata["total_responses"] += 1
    
    def _add_message(self, message: ChatMessage) -> None:
        """Add a message and manage history size."""
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        # Trim history if it exceeds max_history
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context_messages(self) -> List[ChatMessage]:
        """Get recent messages for context (within context window)."""
        if not self.messages:
            return []
        return self.messages[-self.context_window:]
    
    def get_conversation_summary(self) -> str:
        """Generate a summary of the current conversation context."""
        if not self.messages:
            return "New conversation - no previous context."
        
        recent_messages = self.get_context_messages()
        user_messages = [msg.content for msg in recent_messages if msg.role == "user"]
        
        summary_parts = []
        
        if user_messages:
            summary_parts.append(f"Recent questions: {'; '.join(user_messages[-3:])}")
        
        if self.search_context.mentioned_brands:
            summary_parts.append(f"Mentioned brands: {', '.join(self.search_context.mentioned_brands[-5:])}")
        
        if self.search_context.recent_topics:
            summary_parts.append(f"Discussion topics: {', '.join(self.search_context.recent_topics[-5:])}")
        
        if self.search_context.preferred_content_types:
            summary_parts.append(f"Content focus: {', '.join(self.search_context.preferred_content_types[-3:])}")
        
        return " | ".join(summary_parts) if summary_parts else "General conversation about Nestle products."
    
    def get_enhanced_search_params(self) -> Dict[str, Any]:
        """Get search parameters enhanced with conversation context."""
        params = {}
        
        # Suggest content type based on conversation
        if self.search_context.preferred_content_types:
            # Use the most recent content type preference
            params["content_type"] = self.search_context.preferred_content_types[-1]
        
        # Suggest brand filter if consistently mentioned
        if len(self.search_context.mentioned_brands) >= 2:
            # Use the most frequently mentioned brand
            brand_counts = {}
            for brand in self.search_context.mentioned_brands:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            most_mentioned = max(brand_counts.items(), key=lambda x: x[1])
            if most_mentioned[1] >= 2:  # Mentioned at least twice
                params["suggested_brand"] = most_mentioned[0].upper()
        
        # Suggest keywords based on topics
        if self.search_context.recent_topics:
            recent_topic_names = self.search_context.recent_topics[-3:]
            mapped_keywords = self.context_extractor.map_topic_names_to_keywords(recent_topic_names)
            params["suggested_keywords"] = mapped_keywords[:5]  # Limit to 5 keywords
        
        return params
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "max_history": self.max_history,
            "context_window": self.context_window,
            "messages": [msg.to_dict() for msg in self.messages],
            "search_context": self.search_context.to_dict(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationSession":
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            max_history=data.get("max_history", CHAT_CONFIG["max_conversation_history"]),
            context_window=data.get("context_window", CHAT_CONFIG["context_window"])
        )
        
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.metadata = data.get("metadata", {})
        
        # Restore messages
        session.messages = [ChatMessage.from_dict(msg_data) for msg_data in data.get("messages", [])]
        
        # Restore search context
        if "search_context" in data:
            session.search_context = SearchContext.from_dict(data["search_context"])
        
        return session

class SessionManager:
    """Manages multiple conversation sessions and provides session lifecycle functionality."""
    
    def __init__(self, session_timeout_hours: int = None):
        """
        Initialize the session manager.
        
        Args:
            session_timeout_hours (int): Hours after which inactive sessions expire
        """
        self.sessions: Dict[str, ConversationSession] = {}
        timeout_hours = session_timeout_hours or CHAT_CONFIG["session_timeout_hours"]
        self.session_timeout = timedelta(hours=timeout_hours)
    
    def create_session(self, session_id: str = None) -> ConversationSession:
        """Create a new conversation session."""
        session = ConversationSession(session_id=session_id)
        self.sessions[session.session_id] = session
        logger.info(f"Created new session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get an existing session by ID."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session has expired
        if datetime.now() - session.last_activity > self.session_timeout:
            logger.info(f"Session {session_id} expired, removing")
            del self.sessions[session_id]
            return None
        
        return session
    
    def get_or_create_session(self, session_id: str = None) -> ConversationSession:
        """Get existing session or create new one."""
        logger.info(f"get_or_create_session called with session_id: {session_id}")
        logger.info(f"Currently have {len(self.sessions)} active sessions")
        
        if session_id:
            session = self.get_session(session_id)
            if session:
                logger.info(f"Found existing session {session_id} with {len(session.messages)} messages")
                return session
            else:
                logger.info(f"Session {session_id} not found, creating new one")
        
        new_session = self.create_session(session_id)
        logger.info(f"Created new session {new_session.session_id}")
        return new_session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of removed sessions."""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if now - session.last_activity > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_active_sessions_count(self) -> int:
        """Get count of currently active sessions."""
        return len(self.sessions)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about all sessions."""
        if not self.sessions:
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "avg_messages_per_session": 0,
                "oldest_session": None,
                "newest_session": None
            }
        
        total_messages = sum(len(session.messages) for session in self.sessions.values())
        session_ages = [(s.session_id, s.created_at) for s in self.sessions.values()]
        session_ages.sort(key=lambda x: x[1])
        
        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "avg_messages_per_session": total_messages / len(self.sessions),
            "oldest_session": {
                "id": session_ages[0][0],
                "created_at": session_ages[0][1].isoformat()
            } if session_ages else None,
            "newest_session": {
                "id": session_ages[-1][0],
                "created_at": session_ages[-1][1].isoformat()
            } if session_ages else None
        } 