from typing import Dict, List

TOPIC_CATEGORIES = {
    # Food & Beverage Categories
    "chocolate_treats": {
        "name": "Chocolate & Treats",
        "description": "Chocolate products, confectionery, and sweet treats",
        "keywords": [
            "chocolate", "candy", "confectionery", "sweet", "treats", "dessert",
            "cocoa", "truffle", "praline", "caramel", "toffee", "fudge",
            "white chocolate", "dark chocolate", "milk chocolate", "bittersweet",
            "mint chocolate", "orange chocolate", "nuts chocolate"
        ]
    },
    "coffee_beverages": {
        "name": "Coffee & Hot Beverages", 
        "description": "Coffee products, instant beverages, and hot drinks",
        "keywords": [
            "coffee", "espresso", "cappuccino", "latte", "instant coffee",
            "coffee beans", "roasted", "brewing", "barista", "café",
            "hot chocolate", "cocoa", "warm drinks", "beverage", "drink mix"
        ]
    },
    "frozen_desserts": {
        "name": "Frozen Desserts & Ice Cream",
        "description": "Ice cream, frozen treats, and cold desserts", 
        "keywords": [
            "ice cream", "frozen", "gelato", "sorbet", "sherbet", "frozen yogurt",
            "popsicle", "ice bar", "sundae", "cone", "scoop", "dairy",
            "vanilla", "strawberry", "chocolate ice cream", "berry", "tropical",
            "creamy", "smooth", "rich", "indulgent", "refreshing", "cooling"
        ]
    },
    "nutrition_health": {
        "name": "Nutrition & Health",
        "description": "Nutritional products, health supplements, and wellness",
        "keywords": [
            "nutrition", "healthy", "vitamins", "minerals", "protein", "fiber",
            "calcium", "iron", "vitamin c", "vitamin d", "supplements",
            "wellness", "health", "dietary", "nutritious", "balanced",
            "energy", "boost", "immunity", "digestive health", "probiotics"
        ]
    },
    "infant_maternal": {
        "name": "Infant & Maternal Nutrition",
        "description": "Baby food, infant formula, and maternal nutrition",
        "keywords": [
            "baby", "infant", "toddler", "maternal", "pregnancy", "breastfeeding",
            "formula", "baby food", "weaning", "first foods", "organic baby",
            "growth", "development", "pediatric", "newborn", "nursing"
        ]
    },
    "cooking_recipes": {
        "name": "Cooking & Recipes",
        "description": "Recipe content, cooking methods, and meal preparation",
        "keywords": [
            "recipe", "cooking", "baking", "preparation", "ingredients", "method",
            "instructions", "steps", "technique", "kitchen", "meal prep",
            "serving", "portion", "cook time", "prep time", "difficulty",
            "homemade", "scratch", "from scratch", "family recipe"
        ]
    },
    "meal_solutions": {
        "name": "Meal Solutions",
        "description": "Quick meals, convenience foods, and meal preparation",
        "keywords": [
            "quick meal", "easy cooking", "convenient", "instant", "ready to eat",
            "meal kit", "seasoning", "sauce", "bouillon", "soup mix",
            "noodles", "pasta", "rice", "curry", "stir fry", "one pot"
        ]
    },
    "water_hydration": {
        "name": "Water & Hydration", 
        "description": "Water products, hydration, and refreshing beverages",
        "keywords": [
            "water", "sparkling", "mineral water", "spring water", "hydration",
            "refreshing", "pure", "natural", "bubbles", "carbonated",
            "thirst quenching", "crisp", "clean", "fresh"
        ]
    },
    "pet_nutrition": {
        "name": "Pet Nutrition",
        "description": "Pet food, animal nutrition, and pet care",
        "keywords": [
            "pet", "dog", "cat", "puppy", "kitten", "pet food", "animal nutrition",
            "pet care", "veterinary", "healthy pets", "pet treats", "feeding"
        ]
    }
}

# Business themes and corporate topics
BUSINESS_THEMES = {
    "innovation": {
        "name": "Innovation & Technology",
        "description": "Product innovation, research, and technological advancement",
        "keywords": [
            "innovation", "new product", "technology", "research", "development",
            "breakthrough", "advanced", "cutting edge", "pioneering", "discovery",
            "science", "laboratory", "testing", "improvement", "enhanced"
        ]
    },
    "sustainability": {
        "name": "Sustainability & Environment", 
        "description": "Environmental responsibility, sustainable practices, and eco-friendly initiatives",
        "keywords": [
            "sustainability", "sustainable", "environment", "eco-friendly", "green",
            "renewable", "recycling", "carbon footprint", "climate", "biodiversity",
            "responsible sourcing", "ethical", "fair trade", "organic", "natural"
        ]
    },
    "quality": {
        "name": "Quality & Craftsmanship",
        "description": "Product quality, premium ingredients, and craftsmanship",
        "keywords": [
            "quality", "premium", "finest", "craftsmanship", "artisan", "excellence",
            "superior", "high-quality", "best ingredients", "carefully selected",
            "handcrafted", "traditional", "authentic", "pure", "genuine"
        ]
    },
    "community": {
        "name": "Community & Social Responsibility",
        "description": "Community support, social initiatives, and corporate responsibility",
        "keywords": [
            "community", "social responsibility", "giving back", "charitable",
            "foundation", "donation", "support", "helping", "volunteer",
            "education", "youth", "families", "local community", "global impact"
        ]
    },
    "heritage": {
        "name": "Heritage & History",
        "description": "Company history, brand heritage, and traditions",
        "keywords": [
            "heritage", "history", "tradition", "legacy", "founded", "established",
            "generations", "family", "original", "classic", "time-tested",
            "authentic", "trusted", "beloved", "iconic", "timeless"
        ]
    }
}

# Seasonal and occasion-based topics
SEASONAL_TOPICS = {
    "holidays": {
        "name": "Holidays & Celebrations",
        "description": "Holiday-themed content and celebration occasions",
        "keywords": [
            "holiday", "christmas", "valentine", "easter", "halloween", "thanksgiving",
            "celebration", "party", "festive", "seasonal", "special occasion",
            "gift", "sharing", "family gathering", "tradition"
        ]
    },
    "seasonal": {
        "name": "Seasonal Flavors & Products",
        "description": "Season-specific products and limited editions",
        "keywords": [
            "limited edition", "seasonal flavor", "summer", "winter", "spring", "fall",
            "pumpkin spice", "peppermint", "cinnamon", "apple", "berry season",
            "tropical", "citrus", "warming spices", "cooling"
        ]
    }
}

# All topics combined for easy access
ALL_TOPICS = {**TOPIC_CATEGORIES, **BUSINESS_THEMES, **SEASONAL_TOPICS}

def get_topic_category(topic_name: str) -> str:
    """
    Get the category for a given topic name.
    
    Args:
        topic_name (str): The topic name to categorize.
    
    Returns:
        str: The topic category if found, "other" if topic exists but no category,
             or "unknown" if input is None or empty.
    """
    if not topic_name:
        return "unknown"
    
    topic_lower = topic_name.lower().strip()
    
    # Check if topic name matches any category key
    if topic_lower in ALL_TOPICS:
        return topic_lower
    
    # Check if topic name matches any category display name
    for category_key, category_data in ALL_TOPICS.items():
        if topic_lower == category_data["name"].lower():
            return category_key
    
    return "other"

def detect_topics_from_text(text: str, min_keyword_matches: int = 2) -> Dict[str, Dict]:
    """
    Detect topics from text content based on keyword matching.
    
    Args:
        text (str): The text content to analyze.
        min_keyword_matches (int): Minimum number of keyword matches required to classify a topic.
    
    Returns:
        Dict[str, Dict]: Dictionary of detected topics with their match counts and confidence.
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    detected_topics = {}
    
    for topic_key, topic_data in ALL_TOPICS.items():
        matched_keywords = []
        
        for keyword in topic_data["keywords"]:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        match_count = len(matched_keywords)
        
        if match_count >= min_keyword_matches:
            # Calculate confidence based on matches and keyword density
            total_keywords = len(topic_data["keywords"])
            confidence = min(match_count / total_keywords, 1.0) * 100
            
            detected_topics[topic_key] = {
                "name": topic_data["name"],
                "matches": match_count,
                "confidence": round(confidence, 2),
                "matched_keywords": matched_keywords[:5]  # Limit to first 5 matches
            }
    
    # Sort by confidence and match count
    detected_topics = dict(sorted(
        detected_topics.items(),
        key=lambda x: (x[1]["confidence"], x[1]["matches"]),
        reverse=True
    ))
    
    return detected_topics