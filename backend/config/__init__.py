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
    
    validate_config,
    BATCH_SIZE
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

from .scraper import (
    # Compound terms
    FOOD_COMPOUND_TERMS,
    BRAND_COMPOUND_TERMS,
    ALL_COMPOUND_TERMS,
    
    # URLs and project structure
    DEFAULT_BASE_URL,
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    LOGS_DIR,
    DEFAULT_LINKS_FILE,
    DEFAULT_VECTOR_CHUNKS_FILE,
    DEFAULT_CONTENT_INDEX_FILE,
    
    # Content filtering
    EXCLUDE_SECTION_PATTERNS,
    MIN_CONTENT_LENGTH,
    FOOD_INDICATORS,
    GENERIC_TERMS,
    STOP_WORDS,
    
    # Classification indicators
    WEB_COOKIE_INDICATORS,
    FOOD_COOKIE_INDICATORS,
    SOCIAL_MEDIA_INDICATORS,
    FOOD_DOMAINS,
    ERROR_INDICATORS,
    
    # Enhanced filtering patterns
    CONSENT_MANAGEMENT_PATTERNS,
    PRIVACY_CONTENT_INDICATORS,
    
    # Processing settings
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MARKDOWN_CHUNK_SIZE,
    MARKDOWN_CHUNK_OVERLAP,
    MAX_KEYWORDS_PER_CHUNK,
    
    # Scraping settings
    MAX_PAGES_DEFAULT,
    MAX_PAGES_LARGE,
    SCRAPER_CONCURRENCY,
    
    # N-gram settings
    NGRAM_RANGE,
    MAX_NGRAMS,
    MAX_PHRASE_LENGTH,
)

from .azure_ai import (
    # Azure OpenAI configuration
    AZURE_OPENAI_CONFIG,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
    
    # Azure Embedding configuration
    AZURE_EMBEDDING_CONFIG,
    AZURE_EMBEDDING_ENDPOINT,
    AZURE_EMBEDDING_API_KEY,
    AZURE_EMBEDDING_API_VERSION,
    AZURE_EMBEDDING_MODEL_NAME,
    AZURE_EMBEDDING_DEPLOYMENT,
    
    # Chat configuration
    CHAT_CONFIG,
    CHAT_PROMPTS,
    
    # Validation functions
    validate_azure_openai_config,
    validate_azure_embedding_config,
    get_chat_client_config,
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
    "BATCH_SIZE",
    
    # Topics - New structure
    "TOPIC_CATEGORIES",
    "BUSINESS_THEMES", 
    "SEASONAL_TOPICS",
    "ALL_TOPICS",
    
    # Topics - Enhanced functions
    "get_topic_category",
    "detect_topics_from_text",
    
    # Scraper configuration
    "FOOD_COMPOUND_TERMS",
    "BRAND_COMPOUND_TERMS", 
    "ALL_COMPOUND_TERMS",
    "DEFAULT_BASE_URL",
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "LOGS_DIR",
    "DEFAULT_LINKS_FILE",
    "DEFAULT_VECTOR_CHUNKS_FILE",
    "DEFAULT_CONTENT_INDEX_FILE",
    "EXCLUDE_SECTION_PATTERNS",
    "MIN_CONTENT_LENGTH",
    "FOOD_INDICATORS",
    "GENERIC_TERMS",
    "STOP_WORDS",
    "WEB_COOKIE_INDICATORS",
    "FOOD_COOKIE_INDICATORS",
    "SOCIAL_MEDIA_INDICATORS",
    "FOOD_DOMAINS",
    "ERROR_INDICATORS",
    "CONSENT_MANAGEMENT_PATTERNS",
    "PRIVACY_CONTENT_INDICATORS",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",
    "MARKDOWN_CHUNK_SIZE",
    "MARKDOWN_CHUNK_OVERLAP",
    "MAX_KEYWORDS_PER_CHUNK",
    "MAX_PAGES_DEFAULT",
    "MAX_PAGES_LARGE",
    "SCRAPER_CONCURRENCY",
    "NGRAM_RANGE",
    "MAX_NGRAMS",
    "MAX_PHRASE_LENGTH",
    
    # Azure AI configuration
    "AZURE_OPENAI_CONFIG",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY", 
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_EMBEDDING_CONFIG",
    "AZURE_EMBEDDING_ENDPOINT",
    "AZURE_EMBEDDING_BASE_ENDPOINT",
    "AZURE_EMBEDDING_API_KEY",
    "AZURE_EMBEDDING_API_VERSION",
    "AZURE_EMBEDDING_MODEL_NAME",
    "AZURE_EMBEDDING_DEPLOYMENT",
    "CHAT_CONFIG",
    "CHAT_PROMPTS",
    "validate_azure_openai_config",
    "validate_azure_embedding_config",
    "get_chat_client_config",
] 