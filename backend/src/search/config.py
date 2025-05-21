import os
from dotenv import load_dotenv

# Load environment variables.
load_dotenv()

# Azure Cognitive Search settings.
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")

# Index settings.
INDEX_SETTINGS = {
    "name": AZURE_SEARCH_INDEX_NAME,
    "fields": [
        {
            "name": "id",
            "type": "Edm.String",
            "key": True,
            "filterable": True
        },
        {
            "name": "url",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "retrievable": True
        },
        {
            "name": "section_title",
            "type": "Edm.String",
            "searchable": True,
            "retrievable": True
        },
        {
            "name": "doc_index",
            "type": "Edm.Int32",
            "filterable": True,
            "sortable": True,
            "retrievable": True
        },
        {
            "name": "chunk_index",
            "type": "Edm.Int32",
            "filterable": True,
            "sortable": True,
            "retrievable": True
        },
        {
            "name": "total_chunks",
            "type": "Edm.Int32",
            "filterable": True,
            "retrievable": True
        },
        {
            "name": "content",
            "type": "Edm.String",
            "searchable": True,
            "retrievable": True
        },
        {
            "name": "vector",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "retrievable": True,
            "dimensions": 1536,
            "vectorSearchConfiguration": "default"
        },
        {
            "name": "source_file",
            "type": "Edm.String",
            "filterable": True,
            "retrievable": True
        },
        {
            "name": "processed_at",
            "type": "Edm.DateTimeOffset",
            "filterable": True,
            "sortable": True,
            "retrievable": True
        }
    ],
    "vectorSearch": {
        "algorithmConfigurations": [
            {
                "name": "default",
                "kind": "hnsw",
                "parameters": {
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            }
        ]
    },
    "semantic": {
        "configurations": [
            {
                "name": "default",
                "prioritizedFields": {
                    "titleField": {
                        "fieldName": "section_title"
                    },
                    "contentFields": [
                        {
                            "fieldName": "content"
                        }
                    ]
                }
            }
        ]
    }
} 