import re
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime

# Dynamic import to handle both local development and Docker environments
try:
    from backend.config.content_types import CONTENT_TYPE_KEYWORDS
    from backend.config.brands import get_all_brand_variations
    from backend.config.topics import detect_topics_from_text, ALL_TOPICS
except ImportError:
    from config.content_types import CONTENT_TYPE_KEYWORDS
    from config.brands import get_all_brand_variations
    from config.topics import detect_topics_from_text, ALL_TOPICS

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
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
        
        # Extract actual keywords from detected topics
        for topic_data in query_analysis["detected_topics"].values():
            matched_keywords = topic_data.get("matched_keywords", [])
            suggested_keywords.extend(matched_keywords[:2])  # Limit to 2 keywords per topic
        
        # Add context topics if not much detected in current query
        if len(suggested_keywords) < 3 and search_context.recent_topics:
            remaining_slots = 3 - len(suggested_keywords)
            recent_topic_names = search_context.recent_topics[-remaining_slots:]
            mapped_keywords = self.map_topic_names_to_keywords(recent_topic_names)
            suggested_keywords.extend(mapped_keywords)
            if search_context.recent_topics:
                suggestions["context_enhanced"] = True
        
        suggestions["suggested_keywords"] = suggested_keywords[:5]  # Limit to 5 keywords
        
        return suggestions
    
    def map_topic_names_to_keywords(self, topic_names: List[str]) -> List[str]:
        """
        Map topic names to actual keywords that exist in the search index.
        Dynamically extracts keywords from the topic configuration.
        
        Args:
            topic_names (List[str]): List of topic names from context
            
        Returns:
            List[str]: List of actual keywords that can be used for search filtering
        """
        mapped_keywords = []
        
        for topic_name in topic_names:
            # Find the topic configuration by name
            topic_config = None
            for topic_key, topic_data in ALL_TOPICS.items():
                if topic_data["name"] == topic_name:
                    topic_config = topic_data
                    break
            
            if topic_config:
                # Extract keywords from the topic configuration
                # Prioritize keywords that are more likely to exist in search index
                topic_keywords = topic_config.get("keywords", [])
                
                # Filter and prioritize keywords based on common search terms
                prioritized_keywords = []
                for keyword in topic_keywords:
                    # Prioritize shorter, more common terms that are likely in search index
                    if len(keyword.split()) <= 2 and len(keyword) >= 3:
                        prioritized_keywords.append(keyword)
                
                # Add top 3-4 keywords from this topic
                mapped_keywords.extend(prioritized_keywords[:4])
            else:
                # Fallback: extract simple keywords from topic name
                simple_keywords = topic_name.lower().replace(" & ", " ").split()
                mapped_keywords.extend([kw for kw in simple_keywords if len(kw) > 2])
        
        # Remove duplicates while preserving order
        unique_keywords = []
        for keyword in mapped_keywords:
            if keyword not in unique_keywords:
                unique_keywords.append(keyword)
        
        return unique_keywords 