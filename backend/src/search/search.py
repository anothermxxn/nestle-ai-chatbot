import logging
from typing import Dict, List, Optional, Union
from azure.search.documents import SearchClient
# from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set Azure SDK logging to WARNING level to suppress request/response logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class AzureSearchClient:
    """Client for searching documents in Azure Cognitive Search."""
    
    def __init__(self):
        """Initialize the Azure Search client."""
        self.endpoint = AZURE_SEARCH_ENDPOINT
        self.credential = AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=AZURE_SEARCH_INDEX_NAME,
            credential=self.credential
        )

    async def search(
        self,
        query: str = "",
        text_query: Optional[str] = None,
        vectors: Optional[Dict[str, List[float]]] = None,
        filter_expr: Optional[str] = None,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top: int = 10,
        skip: int = 0,
        exhaustive: bool = True
    ) -> List[Dict]:
        """
        Search the index using hybrid search (keyword + vector) with optional filters.
        
        Args:
            query (str): The search query for keyword search.
            text_query (Optional[str]): Text to be converted to vector using the vectorizer.
            vectors (Optional[Dict[str, List[float]]]): Vector embeddings for different fields.
                Example: {"content": [...], "page_title": [...], "section_title": [...]}
            filter_expr (Optional[str]): OData filter expression.
            content_type (Optional[str]): Filter by content type.
            brand (Optional[str]): Filter by brand.
            keywords (Optional[List[str]]): Filter by keywords.
            top (int): Number of results to return.
            skip (int): Number of results to skip for pagination.
            exhaustive (bool): Whether to perform exhaustive vector search.
                When True, searches all vectors. When False, uses approximate search.
            
        Returns:
            List[Dict]: List of search results with the following fields:
                - id: Unique document identifier
                - url: Document URL
                - page_title: Title of the page
                - section_title: Title of the section
                - content: Text content
                - content_type: Type of content
                - brand: Brand name
                - keywords: List of keywords
                - chunk_index: Chunk index within document
                - total_chunks: Total number of chunks in document
        """
        try:
            # Build search options
            search_options = {
                "select": "id,url,page_title,section_title,content,content_type,brand,keywords,doc_index,chunk_index,total_chunks",
                "top": top,
                "skip": skip,
                "include_total_count": True,
                "search_mode": "all"
            }
            
            # Build filter expression
            filters = []
            if filter_expr:
                filters.append(filter_expr)
            if content_type:
                filters.append(f"content_type eq '{content_type}'")
            if brand:
                filters.append(f"brand eq '{brand}'")
            if keywords:
                keyword_filters = [f"keywords/any(k: k eq '{k}')" for k in keywords]
                filters.append(f"({' or '.join(keyword_filters)})")
            
            if filters:
                search_options["filter"] = " and ".join(filters)
            
            # Add vector search configurations
            vector_queries = []
            
            # Add text-based vector queries
            # if text_query:
            #     vector_queries.append(
                    # VectorizableTextQuery(
                    #     kind="text",
                    #     text=text_query,
                    #     k_nearest_neighbors=top,
                    #     fields="content_vector,page_title_vector,section_title_vector",
                    # )
                # )
            
            # Add raw vector queries
            if vectors:
                for field, vector in vectors.items():
                    if vector:
                        vector_queries.append(
                            {
                                "kind": "vector",
                                "vector": vector,
                                "k_nearest_neighbors": top,
                                "fields": f"{field}_vector",
                            }
                            # VectorQuery(
                            #     kind="vector",
                            #     vector=vector,
                            #     k_nearest_neighbors=top,
                            #     fields=f"{field}_vector",
                            # )
                        )
            
            if vector_queries:
                search_options["vector_queries"] = vector_queries
            
            # Perform search
            results = self.client.search(
                search_text=query,
                **search_options
            )
            
            # Convert results to list of dictionaries
            return [dict(result) for result in results]
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise 