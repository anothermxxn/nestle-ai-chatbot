import os
from dotenv import load_dotenv

load_dotenv()

# Azure AI Search settings
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_VERSION = os.getenv("AZURE_SEARCH_API_VERSION")

# Azure AI Search client configuration
SEARCH_CONFIG = {
    "endpoint": AZURE_SEARCH_ENDPOINT,
    "admin_key": AZURE_SEARCH_ADMIN_KEY,
    "index_name": AZURE_SEARCH_INDEX_NAME,
    "api_version": AZURE_SEARCH_API_VERSION
}

# Azure Cosmos DB NoSQL settings
AZURE_COSMOS_ENDPOINT = os.getenv("AZURE_COSMOS_ENDPOINT")
AZURE_COSMOS_KEY = os.getenv("AZURE_COSMOS_KEY")
AZURE_COSMOS_DATABASE_NAME = os.getenv("AZURE_COSMOS_DATABASE_NAME")
ENTITIES_CONTAINER_NAME = os.getenv("AZURE_COSMOS_ENTITIES_CONTAINER_NAME")
RELATIONSHIPS_CONTAINER_NAME = os.getenv("AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME")

# Cosmos DB client configuration
COSMOS_CONFIG = {
    "endpoint": AZURE_COSMOS_ENDPOINT,
    "key": AZURE_COSMOS_KEY,
    "database_name": AZURE_COSMOS_DATABASE_NAME,
    "consistency_level": "Session"
}

# Azure AI Search index configuration
SEARCH_INDEX_SETTINGS = {
    "name": AZURE_SEARCH_INDEX_NAME,
    "fields": [
        # Primary Keys and URLs
        {
            "name": "id",
            "type": "Edm.String",
            "key": True,
            "searchable": False,
            "filterable": True,
            "sortable": False,
            "facetable": False,
            "retrievable": True
        },
        {
            "name": "url",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "sortable": False,
            "facetable": False,
            "retrievable": True
        },
        
        # Content Fields with Vectors
        {
            "name": "content",
            "type": "Edm.String",
            "searchable": True,
            "filterable": False,
            "sortable": False,
            "facetable": False,
            "retrievable": True,
            "analyzer": "standard.lucene"
        },
        {
            "name": "content_vector",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "retrievable": True,
            "dimensions": 1536,
        },
        {
            "name": "page_title",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "sortable": False,
            "facetable": False,
            "retrievable": True,
            "analyzer": "standard.lucene"
        },
        {
            "name": "page_title_vector",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "retrievable": True,
            "dimensions": 1536,
        },
        {
            "name": "section_title",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "sortable": False,
            "facetable": False,
            "retrievable": True
        },
        {
            "name": "section_title_vector",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "retrievable": True,
            "dimensions": 1536,
        },
        
        # Classification Fields
        {
            "name": "content_type",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "sortable": False,
            "facetable": True,
            "retrievable": True
        },
        {
            "name": "brand",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "sortable": False,
            "facetable": True,
            "retrievable": True
        },
        {
            "name": "keywords",
            "type": "Collection(Edm.String)",
            "searchable": True,
            "filterable": True,
            "sortable": False,
            "facetable": True,
            "retrievable": True
        },
        
        # Chunking Information
        {
            "name": "doc_index",
            "type": "Edm.Int32",
            "searchable": False,
            "filterable": True,
            "sortable": True,
            "facetable": False,
            "retrievable": True
        },
        {
            "name": "chunk_index",
            "type": "Edm.Int32",
            "searchable": False,
            "filterable": False,
            "sortable": True,
            "facetable": False,
            "retrievable": True
        },
        {
            "name": "total_chunks",
            "type": "Edm.Int32",
            "searchable": False,
            "filterable": False,
            "sortable": False,
            "facetable": False,
            "retrievable": True
        }
    ],
}

# Graph Database Schemas
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

def validate_config():
    """Validate that all required database configurations are present."""
    
    # Graph Database (Azure Cosmos DB) required variables
    cosmos_vars = [
        ("AZURE_COSMOS_ENDPOINT", AZURE_COSMOS_ENDPOINT),
        ("AZURE_COSMOS_KEY", AZURE_COSMOS_KEY),
        ("AZURE_COSMOS_DATABASE_NAME", AZURE_COSMOS_DATABASE_NAME),
        ("AZURE_COSMOS_ENTITIES_CONTAINER_NAME", ENTITIES_CONTAINER_NAME),
        ("AZURE_COSMOS_RELATIONSHIPS_CONTAINER_NAME", RELATIONSHIPS_CONTAINER_NAME)
    ]
    
    # Vector Database (Azure AI Search) required variables
    search_vars = [
        ("AZURE_SEARCH_ENDPOINT", AZURE_SEARCH_ENDPOINT),
        ("AZURE_SEARCH_ADMIN_KEY", AZURE_SEARCH_ADMIN_KEY),
        ("AZURE_SEARCH_INDEX_NAME", AZURE_SEARCH_INDEX_NAME),
        ("AZURE_SEARCH_API_VERSION", AZURE_SEARCH_API_VERSION)
    ]
    
    # Check for missing variables
    all_vars = cosmos_vars + search_vars
    missing_vars = [name for name, value in all_vars if not value]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True