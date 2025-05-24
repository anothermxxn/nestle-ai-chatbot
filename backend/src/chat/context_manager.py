import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import centralized configurations
try:
    from ...config.content_types import CONTENT_TYPE_KEYWORDS
    from ...config.brands import get_all_brand_variations
    from ...config.topics import detect_topics_from_text
except ImportError:
    from config.content_types import CONTENT_TYPE_KEYWORDS
    from config.brands import get_all_brand_variations
    from config.topics import detect_topics_from_text

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""
    role: str  # "user" or "agent"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ChatMessage":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata")
        )

@dataclass
class SearchContext:
    """Context from previous searches to enhance future queries."""
    recent_topics: List[str]
    preferred_content_types: List[str]
    mentioned_brands: List[str]
    mentioned_products: List[str]
    conversation_themes: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SearchContext":
        """Create from dictionary."""
        return cls(**data)

class ContextExtractor:
    """Extracts context information from user input to enhance search and conversation."""
    
    def __init__(self):
        """Initialize the context extractor with predefined keywords and brands."""
        # Known Nestle brands (from centralized config)
        self.brands = get_all_brand_variations()
        
        # Content type indicators (from centralized config)
        self.content_type_keywords = CONTENT_TYPE_KEYWORDS
    
    def update_search_context(self, user_input: str, search_context: SearchContext) -> None:
        """
        Extract context information from user input and update the search context.
        
        Args:
            user_input (str): The user's input text to analyze
            search_context (SearchContext): The search context to update
        """
        user_input_lower = user_input.lower()
        
        # Update mentioned brands
        self._extract_brands(user_input_lower, search_context)
        
        # Update preferred content types
        self._extract_content_types(user_input_lower, search_context)
        
        # Extract topics/themes using enhanced detection
        self._extract_topics_enhanced(user_input, search_context)
    
    def _extract_brands(self, user_input_lower: str, search_context: SearchContext) -> None:
        """Extract and update mentioned brands from user input."""
        for brand in self.brands:
            if brand in user_input_lower:
                if brand not in search_context.mentioned_brands:
                    search_context.mentioned_brands.append(brand)
                    
                # Keep only recent mentions (last 10)
                if len(search_context.mentioned_brands) > 10:
                    search_context.mentioned_brands = search_context.mentioned_brands[-10:]
    
    def _extract_content_types(self, user_input_lower: str, search_context: SearchContext) -> None:
        """Extract and update preferred content types from user input."""
        for content_type, keywords in self.content_type_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                if content_type not in search_context.preferred_content_types:
                    search_context.preferred_content_types.append(content_type)
                    
                # Keep only recent preferences (last 5)
                if len(search_context.preferred_content_types) > 5:
                    search_context.preferred_content_types = search_context.preferred_content_types[-5:]
    
    def _extract_topics_enhanced(self, user_input: str, search_context: SearchContext) -> None:
        """Extract and update topics/themes using enhanced detection from user input."""
        # Use the new enhanced topic detection
        detected_topics = detect_topics_from_text(user_input, min_keyword_matches=1)
        
        for topic_key, topic_data in detected_topics.items():
            topic_name = topic_data["name"]
            if topic_name not in search_context.recent_topics:
                search_context.recent_topics.append(topic_name)
                
            # Keep only recent topics (last 8)
            if len(search_context.recent_topics) > 8:
                search_context.recent_topics = search_context.recent_topics[-8:]
    
    def analyze_query_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze a user query to determine intent and extract relevant information.
        
        Args:
            user_input (str): The user's query to analyze
            
        Returns:
            Dict[str, Any]: Analysis results including detected intent, brands, topics, etc.
        """
        user_input_lower = user_input.lower()
        
        analysis = {
            "query": user_input,
            "detected_brands": [],
            "detected_topics": {},
            "likely_content_types": [],
            "intent_confidence": {}
        }
        
        # Detect brands
        for brand in self.brands:
            if brand in user_input_lower:
                analysis["detected_brands"].append(brand)
        
        # Detect topics using enhanced detection
        detected_topics = detect_topics_from_text(user_input, min_keyword_matches=1)
        analysis["detected_topics"] = detected_topics
        
        # Detect likely content types with confidence scores
        for content_type, keywords in self.content_type_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in user_input_lower)
            if matches > 0:
                confidence = matches / len(keywords)
                analysis["likely_content_types"].append(content_type)
                analysis["intent_confidence"][content_type] = confidence
        
        return analysis
    
    def get_search_suggestions(self, user_input: str, search_context: SearchContext) -> Dict[str, Any]:
        """
        Generate search suggestions based on user input and conversation context.
        
        Args:
            user_input (str): The current user query
            search_context (SearchContext): The conversation context
            
        Returns:
            Dict[str, Any]: Search suggestions including filters and keywords
        """
        query_analysis = self.analyze_query_intent(user_input)
        
        suggestions = {
            "suggested_content_type": None,
            "suggested_brand": None,
            "suggested_keywords": [],
            "context_enhanced": False
        }
        
        # Suggest content type based on current query
        if query_analysis["likely_content_types"]:
            # Use the content type with highest confidence
            best_content_type = max(
                query_analysis["intent_confidence"].items(),
                key=lambda x: x[1]
            )[0]
            suggestions["suggested_content_type"] = best_content_type
        
        # Suggest brand from current query or context
        if query_analysis["detected_brands"]:
            suggestions["suggested_brand"] = query_analysis["detected_brands"][0].upper()
        elif search_context.mentioned_brands:
            # Use most recently mentioned brand from context
            suggestions["suggested_brand"] = search_context.mentioned_brands[-1].upper()
            suggestions["context_enhanced"] = True
        
        # Suggest keywords from current query and context
        suggested_keywords = []
        suggested_keywords.extend(query_analysis["detected_topics"].keys())
        
        # Add context topics if not much detected in current query
        if len(suggested_keywords) < 3 and search_context.recent_topics:
            remaining_slots = 3 - len(suggested_keywords)
            suggested_keywords.extend(search_context.recent_topics[-remaining_slots:])
            if search_context.recent_topics:
                suggestions["context_enhanced"] = True
        
        suggestions["suggested_keywords"] = suggested_keywords[:5]  # Limit to 5 keywords
        
        return suggestions 