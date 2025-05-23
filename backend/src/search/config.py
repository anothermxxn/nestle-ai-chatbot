import os
from dotenv import load_dotenv

# Load environment variables.
load_dotenv()

# Azure Cognitive Search settings.
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_SEARCH_API_VERSION = os.getenv("AZURE_SEARCH_API_VERSION")

# Azure Embedding API settings.
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION")
AZURE_EMBEDDING_MODEL_NAME = os.getenv("AZURE_EMBEDDING_MODEL_NAME")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")

# Index settings.
INDEX_SETTINGS = {
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
        },
        {
            "name": "processed_at",
            "type": "Edm.DateTimeOffset",
            "searchable": False,
            "filterable": True,
            "sortable": True,
            "facetable": False,
            "retrievable": True
        }
    ],
} 