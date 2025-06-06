try:
    from backend.config.brands import get_all_brand_variations
except ImportError:
    from config.brands import get_all_brand_variations

# Amazon Product Search API Configuration
AMAZON_SEARCH_CONFIG = {
    "base_url": "https://www.amazon.ca",
    "search_endpoint": "/s",
    "timeout": 15,
    "max_results": 3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    "default_department": "grocery",
    "search_params": {
        "k": "",  # search query
        "ref": "sr_nr_n_1",
        "rh": "n:6967212011",  # Grocery & Gourmet Food department
        "sort": "relevanceblender",
    }
}

# Amazon URL generation patterns
AMAZON_URL_PATTERNS = {
    "search_url": "https://www.amazon.ca/s?k={query}&rh=n:6967212011&ref=sr_nr_n_1",
    "product_url": "https://www.amazon.ca/dp/{asin}",
    "affiliate_url": "https://www.amazon.ca/dp/{asin}?tag={affiliate_tag}",
}

# Product parsing selectors and patterns
AMAZON_SELECTORS = {
    "product_container": "[data-component-type='s-search-result']",
    "title": "h2 a span",
    "price": ".a-price-whole",
    "rating": ".a-icon-alt",
    "image": ".s-image",
    "url": "h2 a",
    "sponsored": "[data-component-type='s-search-result'] .puis-sponsored-label-text",
}

# Enhanced category search parameters using brand categories
CATEGORY_SEARCH_PARAMS = {
    # Map brand categories to Amazon department IDs
    "treat": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    "coffee": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food  
        "sort": "relevanceblender"
    },
    "frozen": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    "infant": {
        "rh": "n:6205124011",  # Baby Products
        "sort": "relevanceblender"
    },
    "meal": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    "nutrition": {
        "rh": "n:3760901",  # Health & Personal Care
        "sort": "relevanceblender"
    },
    "pet": {
        "rh": "n:6291457011",  # Pet Supplies
        "sort": "relevanceblender"
    },
    "drink": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    "water": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    # Fallback categories for common search types
    "food": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    "beverage": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food  
        "sort": "relevanceblender"
    },
    "snack": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    },
    "baby": {
        "rh": "n:6205124011",  # Baby Products
        "sort": "relevanceblender"
    },
    "default": {
        "rh": "n:6967212011",  # Grocery & Gourmet Food
        "sort": "relevanceblender"
    }
}

# Category detection keywords for search categorization
CATEGORY_DETECTION_KEYWORDS = {
    "infant": [
        "baby", "infant", "formula", "materna", "nido", "newborn", 
        "feeding", "nutrition baby", "baby food", "baby milk"
    ],
    "pet": [
        "dog", "cat", "pet", "puppy", "kitten", "animal", "canine", 
        "feline", "pet food", "dog food", "cat food", "pet treats"
    ],
    "coffee": [
        "coffee", "espresso", "cappuccino", "nescafe", "nescafé", 
        "instant coffee", "ground coffee", "coffee beans", "caffeine"
    ],
    "treat": [
        "chocolate", "candy", "snack", "sweet", "kit kat", "smarties", 
        "aero", "after eight", "quality street", "rolo", "turtles"
    ],
    "drink": [
        "drink", "beverage", "juice", "tea", "nestea", "nesquik", 
        "iced tea", "fruit drink", "refreshment"
    ],
    "water": [
        "water", "sparkling", "perrier", "pellegrino", "san pellegrino", 
        "mineral water", "sparkling water", "bottled water"
    ],
    "nutrition": [
        "boost", "supplement", "vitamin", "health", "protein", 
        "nutritional", "wellness", "dietary supplement"
    ],
    "frozen": [
        "frozen", "ice cream", "frozen treat", "drumstick", 
        "häagen-dazs", "frozen dessert"
    ],
    "meal": [
        "meal", "maggi", "seasoning", "soup", "instant", 
        "quick meal", "ready meal"
    ]
}

# Error handling configuration
ERROR_HANDLING = {
    "max_retries": 3,
    "retry_delay": 2,  # seconds
    "backoff_factor": 1.5,
    "timeout_errors": ["TimeoutError", "ConnectTimeout", "ReadTimeout"],
    "rate_limit_delay": 5,  # seconds to wait on rate limiting
}

# Generate valid product indicators from brand data
def _generate_valid_product_indicators():
    """Generate valid product indicators from brand patterns."""
    indicators = set()
    
    # Add all brand variations (lowercased for matching)
    all_variations = get_all_brand_variations()
    for variation in all_variations:
        indicators.add(variation.lower())
    
    # Add common Nestlé-related terms
    additional_terms = [
        "nestle", "nestlé", "nescafe", "nespresso", "gerber", 
        "stouffer", "lean cuisine", "hot pockets", "digiorno", 
        "tombstone", "buitoni", "libby", "carnation",
        "fancy feast", "friskies", "beneful", "pro plan",
        "cat chow", "dog chow", "tidy cats", "felix"
    ]
    
    for term in additional_terms:
        indicators.add(term.lower())
    
    return sorted(list(indicators))
VALID_PRODUCT_INDICATORS = _generate_valid_product_indicators()

# Product quality filters
EXCLUDE_PRODUCT_KEYWORDS = [
    "generic", "off-brand", "knockoff", "imitation", "replica", "counterfeit",
    "used", "damaged", "expired", "recalled", "fake", "unauthorized"
]

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 30,
    "requests_per_hour": 300,
    "burst_limit": 10,
    "cooldown_period": 60,  # seconds
}

# Brand category mapping function
def get_amazon_category_for_brand(brand_name: str) -> str:
    """
    Get the appropriate Amazon search category for a given brand.
    
    Args:
        brand_name: Brand name to categorize
        
    Returns:
        Category name for Amazon search parameters
    """
    try:
        from backend.config.brands import get_brand_category
    except ImportError:
        from config.brands import get_brand_category
    
    brand_category = get_brand_category(brand_name)
    
    # Map brand categories to search categories
    if brand_category in CATEGORY_SEARCH_PARAMS:
        return brand_category
    elif brand_category == "other":
        return "food"  # Default to food for unknown Nestlé brands
    else:
        return "default" 