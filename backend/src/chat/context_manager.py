import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

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
        # Known Nestle brands
        self.brands = [
            "del monte", "maggi", "drumstick", "nestea", "perrier", "coffee crisp",
            "quality street", "nescafe", "aero", "boost", "after eight", "carnation",
            "coffee-mate", "turtles", "haagen-dazs", "häagen-dazs", "kit kat", "kitkat", 
            "big turk", "smarties", "milo", "materna", "crunch", "real dairy", "nature's bounty",
            "gerber", "parlour", "nesfruta", "mackintosh", "nesquik", "nido", "mirage",
            "rolo", "ibgard", "purina", "oreo"
        ]
        
        # Content type indicators
        self.content_type_keywords = {
            "recipe": [
                "recipe", "cook", "bake", "prepare", "ingredient", "how to make",
                "ingredients", "directions", "instructions", "servings", "total time",
                "prep", "assembly", "tips", "cooking time", "prep time", "method",
                "steps", "procedure", "technique"
            ],
            "brand": [
                "product", "brand", "about", "tell me about", "features", "benefits",
                "nutrition information", "calories", "crafted", "made with", 
                "frozen dessert", "cones", "nutrition facts", "varieties",
                "flavors", "flavours", "description", "details"
            ],
            "news": [
                "news", "latest", "update", "announcement", "new", "launch",
                "release", "coming soon", "available now"
            ],
            "other": [
                "company", "nestle", "history", "about nestle", "corporate",
                "values", "mission", "story", "heritage"
            ],
            "sustainability": [
                "sustainability", "sustainable", "environment", "eco", "green", 
                "carbon", "renewable", "recycling", "climate", "responsible",
                "environmental impact", "eco-friendly", "organic", "natural"
            ]
        }
        
        # Extract topics/themes
        self.topic_keywords = [
            # Basic food categories
            "chocolate", "coffee", "cookie", "cake", "dessert", "baking", "cooking", "nutrition",
            
            # Frozen desserts & ice cream
            "frozen", "ice cream", "sorbet", "gelato", "bars", "popsicles", "cones", "sundae",
            
            # Flavors from chunks
            "caramel", "vanilla", "strawberry", "mango", "berry", "coconut", "pineapple", 
            "raspberry", "truffle", "white chocolate", "lemon", "tropical", "mint",
            
            # Savory foods
            "noodles", "masala", "curry", "soup", "tacos", "rice", "biryani", "pasta",
            "bouillon", "seasoning", "sauce", "spicy", "chilli", "garlic",
            
            # Dessert types
            "meringue", "pavlova", "coulis", "brownie", "cheesecake", "mousse", "tart",
            
            # Cooking descriptors
            "sweet", "salty", "creamy", "crispy", "smooth", "rich", "delicious",
            "refreshing", "indulgent", "decadent",
            
            # Cooking methods & terms
            "preparation", "serving", "assembly", "mixing", "whipping", "melting",
            "freezing", "chilling", "heating", "boiling", "simmering",
            
            # Dietary & nutrition
            "healthy", "protein", "fiber", "vitamins", "calories", "fat", "sugar",
            "dairy", "plant-based", "vegetarian", "organic", "natural"
        ]
    
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
        
        # Extract topics/themes
        self._extract_topics(user_input_lower, search_context)
    
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
    
    def _extract_topics(self, user_input_lower: str, search_context: SearchContext) -> None:
        """Extract and update topics/themes from user input."""
        for keyword in self.topic_keywords:
            if keyword in user_input_lower:
                if keyword not in search_context.recent_topics:
                    search_context.recent_topics.append(keyword)
                    
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
            "detected_topics": [],
            "likely_content_types": [],
            "intent_confidence": {}
        }
        
        # Detect brands
        for brand in self.brands:
            if brand in user_input_lower:
                analysis["detected_brands"].append(brand)
        
        # Detect topics
        for topic in self.topic_keywords:
            if topic in user_input_lower:
                analysis["detected_topics"].append(topic)
        
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
        suggested_keywords.extend(query_analysis["detected_topics"])
        
        # Add context topics if not much detected in current query
        if len(suggested_keywords) < 3 and search_context.recent_topics:
            remaining_slots = 3 - len(suggested_keywords)
            suggested_keywords.extend(search_context.recent_topics[-remaining_slots:])
            if search_context.recent_topics:
                suggestions["context_enhanced"] = True
        
        suggestions["suggested_keywords"] = suggested_keywords[:5]  # Limit to 5 keywords
        
        return suggestions 