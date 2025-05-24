from .content_types import (
    CONTENT_TYPES,
    CONTENT_TYPE_KEYWORDS,
    CONTENT_TYPE_CATEGORIES
)

from .brands import (
    BRAND_PATTERNS,
    NESTLE_BRANDS,
    BRAND_CATEGORIES,
    normalize_brand_name,
    get_brand_category,
    get_all_brand_variations
)

from .database import (
    # Graph Database (Azure Cosmos DB)
    COSMOS_CONFIG,
    CONTAINER_CONFIGS,
    ENTITY_TYPES,
    RELATIONSHIP_TYPES,
    
    # Vector Database (Azure AI Search)
    SEARCH_CONFIG,
    EMBEDDING_CONFIG,
    SEARCH_INDEX_SETTINGS,
    
    # Environment Variables
    AZURE_COSMOS_ENDPOINT,
    AZURE_COSMOS_KEY,
    AZURE_COSMOS_DATABASE_NAME,
    ENTITIES_CONTAINER_NAME,
    RELATIONSHIPS_CONTAINER_NAME,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY,
    AZURE_SEARCH_INDEX_NAME,
    AZURE_SEARCH_API_VERSION,
    
    # Validation Functions
    validate_config,
)

from .topics import (
    # New comprehensive structure
    TOPIC_CATEGORIES,
    BUSINESS_THEMES,
    SEASONAL_TOPICS,
    ALL_TOPICS,
    
    # Enhanced functions
    get_topic_category,
    detect_topics_from_text,
)

__all__ = [
    # Content Types
    "CONTENT_TYPES",
    "CONTENT_TYPE_KEYWORDS", 
    "CONTENT_TYPE_CATEGORIES",
    
    # Brands
    "BRAND_PATTERNS",
    "NESTLE_BRANDS",
    "BRAND_CATEGORIES",
    "normalize_brand_name",
    "get_brand_category",
    "get_all_brand_variations",
    
    # Database
    "COSMOS_CONFIG",
    "CONTAINER_CONFIGS",
    "ENTITY_TYPES",
    "RELATIONSHIP_TYPES",
    "SEARCH_CONFIG",
    "SEARCH_INDEX_SETTINGS",
    "AZURE_COSMOS_ENDPOINT",
    "AZURE_COSMOS_KEY",
    "AZURE_COSMOS_DATABASE_NAME",
    "ENTITIES_CONTAINER_NAME",
    "RELATIONSHIPS_CONTAINER_NAME",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_ADMIN_KEY",
    "AZURE_SEARCH_INDEX_NAME",
    "AZURE_SEARCH_API_VERSION",
    "validate_config",
    
    # Topics - New structure
    "TOPIC_CATEGORIES",
    "BUSINESS_THEMES", 
    "SEASONAL_TOPICS",
    "ALL_TOPICS",
    
    # Topics - Enhanced functions
    "get_topic_category",
    "detect_topics_from_text",
] 