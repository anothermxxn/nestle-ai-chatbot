import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure Cosmos DB NoSQL settings
AZURE_COSMOS_ENDPOINT = os.getenv("AZURE_COSMOS_ENDPOINT")
AZURE_COSMOS_KEY = os.getenv("AZURE_COSMOS_KEY")
AZURE_COSMOS_DATABASE_NAME = os.getenv("AZURE_COSMOS_DATABASE_NAME")
ENTITIES_CONTAINER_NAME = os.getenv("AZURE_COSMOS_ENTITIES_CONTAINER_NAME")
RELATIONSHIPS_CONTAINER_NAME = os.getenv("AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME")

# Entity types configuration
ENTITY_TYPES = {
    "Brand": {
        "description": "A brand entity extracted from content",
        "properties": ["name", "description", "category", "content_types", "chunk_count", "chunk_ids"],
        "required": ["name"],
        "partition_key": "category"
    },
    "Topic": {
        "description": "A topic or theme extracted from content",
        "properties": ["name", "description", "category", "keywords", "chunk_count", "chunk_ids"],
        "required": ["name", "category"],
        "partition_key": "category"
    },
    "Product": {
        "description": "A product mentioned in content",
        "properties": ["name", "brand", "category", "description", "chunk_count", "chunk_ids"],
        "required": ["name"],
        "partition_key": "brand"
    },
    "Recipe": {
        "description": "A recipe entity with ingredients and instructions",
        "properties": ["title", "recipe_type", "keywords", "ingredients_mentioned", "chunk_count", "chunk_ids"],
        "required": ["title"],
        "partition_key": "recipe_type"
    }
}

# Relationship types configuration
RELATIONSHIP_TYPES = {
    "BELONGS_TO": {
        "description": "Product belongs to Brand",
        "from_types": ["Product"],
        "to_types": ["Brand"]
    },
    "MENTIONS": {
        "description": "Topic/Product mentioned in Brand content",
        "from_types": ["Topic", "Product"],
        "to_types": ["Brand"]
    },
    "CONTAINS": {
        "description": "Recipe contains specific products",
        "from_types": ["Recipe"],
        "to_types": ["Product"]
    },
    "RELATED_TO": {
        "description": "Generic relationship between similar entities",
        "from_types": ["Product", "Recipe", "Topic", "Brand"],
        "to_types": ["Product", "Recipe", "Topic", "Brand"]
    },
    "FEATURED_IN": {
        "description": "Brand/Product featured in specific topics",
        "from_types": ["Brand", "Product"],
        "to_types": ["Topic"]
    }
}

# Content types configuration
CONTENT_TYPE_CATEGORIES = {
    "brand": "Brand Information",
    "recipe": "Recipe Content",
    "news": "News & Updates",
    "other": "General Content"
}

# Brands configuration
NESTLE_BRANDS = [
    "BOOST",
    "KIT KAT",
    "DRUMSTICK",
    "TURTLES",
    "MAGGI",
    "NESCAFE",
    "COFFEE CRISP",
    "AERO",
    "COFFEE-MATE",
    "CARNATION",
    "SMARTIES",
    "PARLOUR",
    "AFTER EIGHT",
    "QUALITY STREET",
    "DEL MONTE",
    "REAL DAIRY",
    "CRUNCH",
    "NESQUIK",
    "MILO",
    "NATURE'S BOUNTY",
    "NESTEA",
    "HAAGEN-DAZS",
    "NESFRUTA",
    "MATERNA",
    "BIG TURK",
    "MACKINTOSH TOFFEE",
    "MIRAGE",
    "ROLO",
    "PERRIER",
    "GERBER",
    "NIDO",
    "PURINA"
]

# Brand categories configuration
BRAND_CATEGORIES = {
    # Chocolate & Treats
    "treat": ["AERO", "AFTER EIGHT", "BIG TURK", "COFFEE CRISP", "CRUNCH", 
              "DRUMSTICK BITES", "KIT KAT", "MACKINTOSH TOFFEE", "MIRAGE", 
              "QUALITY STREET", "ROLO", "SMARTIES", "TURTLES"],
    
    # Coffee
    "coffee": ["COFFEE-MATE", "NESCAFE"],
    
    # Ice Cream & Frozen Treats  
    "frozen": ["DEL MONTE", "DRUMSTICK", "HAAGEN-DAZS", "PARLOUR", "REAL DAIRY"],
    
    # Infant Nutrition
    "infant": ["MATERNA", "NIDO"],
    
    # Meal Times Made Easy
    "meal": ["MAGGI"],
    
    # Nutrition +
    "nutrition": ["BOOST", "BOOST KIDS", "IBGARD", "NATURE'S BOUNTY"],
    
    # Pet Foods
    "pet": ["PURINA"],
    
    # Quick-Mix Drinks
    "drink": ["CARNATION", "GOODHOST", "MILO", "NESTEA", "NESFRUTA", "NESQUIK"],
    
    # Spring & Sparkling Water
    "water": ["MAISON PERRIER", "PERRIER", "SAN PELLEGRINO"]
}

# Topics configuration
COMMON_TOPICS = {
    "recipes": ["cooking", "baking", "meal prep", "ingredients", "kitchen tips"],
    "nutrition": ["health", "wellness", "vitamins", "dietary", "nutrition facts"],
    "sustainability": ["environment", "eco-friendly", "responsible sourcing", "planet"],
    "innovation": ["new products", "technology", "research", "development"],
    "community": ["social responsibility", "community support", "charitable"],
    "quality": ["premium", "quality ingredients", "craftsmanship", "standards"]
}

# Cosmos DB client configuration
COSMOS_CONFIG = {
    "endpoint": AZURE_COSMOS_ENDPOINT,
    "key": AZURE_COSMOS_KEY,
    "database_name": AZURE_COSMOS_DATABASE_NAME,
    "consistency_level": "Session"
}

# Container configurations
CONTAINER_CONFIGS = {
    ENTITIES_CONTAINER_NAME: {
        "partition_key": "/entity_type",
        "throughput": 400
    },
    RELATIONSHIPS_CONTAINER_NAME: {
        "partition_key": "/relationship_type", 
        "throughput": 400
    }
}

def get_brand_category(brand_name: str) -> str:
    """Get the category for a given brand name."""
    if not brand_name:
        return "unknown"
    
    brand_upper = brand_name.upper()
    for category, brands in BRAND_CATEGORIES.items():
        if brand_upper in brands:
            return category
    return "other"

def normalize_brand_name(brand_name: str) -> str:
    """Normalize brand name to match the expected format."""
    if not brand_name:
        return None
    
    # Convert to uppercase and strip whitespace
    normalized = brand_name.upper().strip()
    
    # Handle common variations
    brand_mappings = {
        "COFFEE MATE": "COFFEE-MATE",
        "COFFEEMATE": "COFFEE-MATE",
        "HAAGEN DAZS": "HAAGEN-DAZS", 
        "HAAGEN_DAZS": "HAAGEN-DAZS",
        "KITKAT": "KIT KAT",
        "KIT-KAT": "KIT KAT",
        "AFTER-EIGHT": "AFTER EIGHT",
        "BIG-TURK": "BIG TURK",
        "COFFEE-CRISP": "COFFEE CRISP",
        "QUALITY-STREET": "QUALITY STREET",
        "MACKINTOSH-TOFFEE": "MACKINTOSH TOFFEE",
        "NATURES BOUNTY": "NATURE'S BOUNTY",
        "NATURE'S-BOUNTY": "NATURE'S BOUNTY",
        "BOOST-KIDS": "BOOST KIDS",
        "NESTLÉ MATERNA": "MATERNA",
        "NESTLE MATERNA": "MATERNA",
        "MAISON-PERRIER": "MAISON PERRIER",
        "SAN-PELLEGRINO": "SAN PELLEGRINO",
    }
    
    # Apply mappings
    if normalized in brand_mappings:
        normalized = brand_mappings[normalized]
    
    return normalized if normalized in NESTLE_BRANDS else normalized

def extract_topics_from_keywords(keywords: list) -> list:
    """Extract relevant topics from content keywords."""
    topics = []
    
    if not keywords:
        return topics
    
    keywords_lower = [k.lower() for k in keywords]
    
    for topic, topic_keywords in COMMON_TOPICS.items():
        # Check if any topic keywords appear in content keywords
        if any(tk in " ".join(keywords_lower) for tk in topic_keywords):
            topics.append(topic)
    
    return topics

def validate_config():
    """Validate that all required configuration is present."""
    required_vars = [
        ("AZURE_COSMOS_ENDPOINT", AZURE_COSMOS_ENDPOINT),
        ("AZURE_COSMOS_KEY", AZURE_COSMOS_KEY),
        ("AZURE_COSMOS_DATABASE_NAME", AZURE_COSMOS_DATABASE_NAME),
        ("AZURE_COSMOS_ENTITIES_CONTAINER_NAME", ENTITIES_CONTAINER_NAME),
        ("AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME", RELATIONSHIPS_CONTAINER_NAME)
    ]
    
    missing_vars = [name for name, value in required_vars if not value]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True 