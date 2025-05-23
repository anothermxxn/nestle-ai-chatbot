from .chat_client import NestleChatClient
from .chat_router import router as chat_router
from .context_manager import ChatMessage, SearchContext, ContextExtractor
__version__ = "1.0.0"
__all__ = ["NestleChatClient", "chat_router"] 