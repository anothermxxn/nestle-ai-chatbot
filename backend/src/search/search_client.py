from datetime import datetime
import logging
from typing import Dict, List, Optional
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from azure.core.credentials import AzureKeyCredential
from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY,
    AZURE_SEARCH_INDEX_NAME
)
from relevance_scorer import VectorSearchRanker

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
    """Client for searching documents in Azure Cognitive Search with enhanced vector ranking."""
    
    def __init__(self, enable_enhanced_ranking: bool = True):
        """
        Initialize the Azure Search client.
        
        Args:
            enable_enhanced_ranking (bool): Whether to enable enhanced relevance ranking on top of vector search
        """
        self.endpoint = AZURE_SEARCH_ENDPOINT
        self.credential = AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=AZURE_SEARCH_INDEX_NAME,
            credential=self.credential
        )
        
        # Initialize enhanced ranker if enabled
        self.enable_enhanced_ranking = enable_enhanced_ranking
        if enable_enhanced_ranking:
            self.ranker = VectorSearchRanker()
        else:
            self.ranker = None

    def _prepare_document(self, document: Dict) -> Dict:
            """
            Prepare document for indexing by:
            1. Adding a unique id field
            2. Converting processed_at to Azure Search format
            
            Args:
                document (Dict): Document to prepare.
                
            Returns:
                Dict: Prepared document.
            """
            doc = document.copy()
            
            # Generate unique id from url, doc_index, and chunk_index
            doc["id"] = f"{doc['url']}_{doc['doc_index']}_{doc['chunk_index']}".replace("/", "_")
            
            if "processed_at" in doc:
                # Convert ISO format to Azure Search format
                try:
                    # Parse the ISO datetime string
                    dt = datetime.fromisoformat(doc["processed_at"])
                    # Format for Azure Search
                    doc["processed_at"] = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"
                except Exception as e:
                    logger.error(f"Error formatting processed_at: {str(e)}")
                    raise
            
            return doc
        
    async def index_documents(self, documents: List[Dict]) -> bool:
        """
        Index a batch of documents.
        
        Args:
            documents (List[Dict]): List of documents to index.
            
        Returns:
            bool: True if all documents were indexed successfully, False otherwise.
        """
        try:
            if not documents:
                logger.warning("No documents to index")
                return True
                
            # Process in batches of 100 (Azure Search recommended batch size)
            batch_size = 100
            total_documents = len(documents)
            total_batches = (total_documents + batch_size - 1) // batch_size
            overall_success = True
            total_successful = 0
            total_failed = 0
            
            logger.info(f"Starting upload of {total_documents} documents in {total_batches} batches")
            
            for i in range(0, total_documents, batch_size):
                batch_num = i // batch_size + 1
                batch = documents[i:i + batch_size]
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
                
                # Prepare documents
                prepared_batch = [self._prepare_document(doc) for doc in batch]
                
                # Upload the batch
                results = self.client.upload_documents(documents=prepared_batch)
                
                # Check results
                successful = [r for r in results if r.succeeded]
                failed = [r for r in results if not r.succeeded]
                
                total_successful += len(successful)
                total_failed += len(failed)
                
                if failed:
                    logger.error(f"Batch {batch_num}: {len(failed)} documents failed to upload")
                    for result in failed[:3]:  # Log first 3 failures
                        logger.error(f"Failed: {result.key} - {result.error_message}")
                    if len(failed) > 3:
                        logger.error(f"... and {len(failed) - 3} more failures")
                    overall_success = False
                else:
                    logger.info(f"Batch {batch_num}: All {len(successful)} documents uploaded successfully")
                        
            # Final summary
            logger.info(f"Upload complete: {total_successful} successful, {total_failed} failed")
            return overall_success
                
        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            return False

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
        exhaustive: bool = True,
        enable_ranking: bool = True,
        custom_boosts: Optional[Dict[str, float]] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Search the index using hybrid search (keyword + vector) with optional enhanced ranking.
        
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
            enable_ranking (bool): Whether to apply enhanced relevance ranking on top of vector scores.
            custom_boosts (Optional[Dict[str, float]]): Custom boost factors for ranking.
            custom_weights (Optional[Dict[str, float]]): Custom weight adjustments for ranking.
            
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
                - @search.score: Original Azure Search score (vector + BM25)
                - relevance_score: Enhanced relevance score (if ranking enabled)
                - original_vector_score: Normalized vector similarity score (if ranking enabled)
                - score_breakdown: Detailed scoring breakdown (if ranking enabled)
        """
        try:
            # Build search options
            search_options = {
                "select": "id,url,page_title,section_title,content,content_type,brand,keywords,doc_index,chunk_index,total_chunks,processed_at",
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
            if text_query:
                vector_queries.append(
                    VectorizableTextQuery(
                        kind="text",
                        text=text_query,
                        k_nearest_neighbors=top,
                        fields="content_vector,page_title_vector,section_title_vector",
                        exhaustive=exhaustive,
                    )
                )
            
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
                                "exhaustive": exhaustive,
                            }
                        )
            
            if vector_queries:
                search_options["vector_queries"] = vector_queries
            
            # Perform search
            results = self.client.search(
                search_text=query,
                **search_options
            )
            
            # Convert results to list of dictionaries
            search_results = [dict(result) for result in results]
            
            # Apply enhanced ranking if enabled
            if enable_ranking and self.enable_enhanced_ranking and self.ranker:
                search_query = query or text_query or ""
                search_results = self.ranker.rank_results(
                    query=search_query,
                    results=search_results,
                    custom_boosts=custom_boosts,
                    custom_weights=custom_weights
                )
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise 