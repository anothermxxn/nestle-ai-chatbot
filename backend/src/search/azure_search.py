import logging
from typing import Dict, List, Optional
from datetime import datetime
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from .config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY,
    AZURE_SEARCH_INDEX_NAME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AzureSearchClient:
    """Client for interacting with Azure Cognitive Search."""
    
    def __init__(self):
        """Initialize the Azure Search client."""
        self.endpoint = AZURE_SEARCH_ENDPOINT
        self.credential = AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
        self.client = SearchClient(
            endpoint=self.endpoint,
            index_name=AZURE_SEARCH_INDEX_NAME,
            credential=self.credential
        )

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
            # Process in batches of 100
            batch_size = 100
            success = True
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Prepare documents
                prepared_batch = [self._prepare_document(doc) for doc in batch]
                logger.info(f"Prepared batch {i//batch_size + 1} with {len(prepared_batch)} documents")
                logger.info(f"Sample document: {prepared_batch[0] if prepared_batch else 'No documents'}")
                
                # Upload the batch directly
                results = self.client.upload_documents(documents=prepared_batch)
                
                # Check if any documents failed
                failed = [r for r in results if not r.succeeded]
                if failed:
                    logger.error(f"Batch {i//batch_size + 1}: Failed to index {len(failed)} documents")
                    for result in failed:
                        logger.error(f"Failed document: {result.key}, Error: {result.error_message}")
                    success = False
                else:
                    logger.info(f"Batch {i//batch_size + 1}: Successfully indexed {len(batch)} documents")
                    logger.info(f"First document status: {results[0].status_code}")
                        
            return success
                
        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            return False
    
    async def search(
        self,
        query: str,
        vector: Optional[List[float]] = None,
        filter_expr: Optional[str] = None,
        top: int = 10,
        skip: int = 0
    ) -> List[Dict]:
        """
        Search the index using vector search with optional filters.
        
        Args:
            query (str): The search query.
            vector (Optional[List[float]]): Vector embedding for vector search.
            filter_expr (Optional[str]): OData filter expression.
            top (int): Number of results to return.
            skip (int): Number of results to skip for pagination.
            
        Returns:
            List[Dict]: List of search results.
        """
        try:
            # Build search options
            search_options = {
                "select": "id,url,section_title,content,source_file",
                "top": top,
                "skip": skip,
                "include_total_count": True
            }
            
            if vector:
                search_options["vectors"] = [{
                    "value": vector,
                    "fields": "vector",
                    "k": top
                }]
            
            if filter_expr:
                search_options["filter"] = filter_expr
            
            # Perform search
            results = self.client.search(
                search_text=query,
                **search_options
            )
            
            # Convert results to list and ensure all fields are present
            return [dict(result) for result in results]
                
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return [] 