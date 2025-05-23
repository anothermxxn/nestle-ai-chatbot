import asyncio
import logging
import numpy as np
from typing import Dict, List
from search_client import AzureSearchClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set Azure SDK logging to WARNING level to suppress request/response logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def generate_test_vector(dim: int = 1536) -> List[float]:
    """Generate a random test vector of specified dimension."""
    return list(np.random.rand(dim).astype(float))

async def test_keyword_search():
    """Test basic keyword search without vectors."""
    try:
        client = AzureSearchClient()
        query = "kit kat"
        logger.info(f"\nTesting keyword search with query: '{query}'")
        
        results = await client.search(
            query=query,
            top=3
        )
        
        logger.info(f"Found {len(results)} results for keyword search")
        
        # Print detailed results
        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Title: {result.get('page_title', 'N/A')} \"{result.get('section_title', 'N/A')}\"")
            logger.info(f"Content Type: {result.get('content_type', 'N/A')}")
            logger.info(f"Score: {result.get('@search.score', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error in Keyword Search: {str(e)}")

async def test_vector_search():
    """Test vector search with random vectors."""
    try:
        client = AzureSearchClient()
        logger.info("\nTesting vector search with random vectors")
        
        # Generate random vectors for testing
        content_vector = generate_test_vector()
        page_title_vector = generate_test_vector()
        
        vectors = {
            "content": content_vector,
            "page_title": page_title_vector
        }
        
        logger.info(f"Vector dimensions: content={len(content_vector)}, page_title={len(page_title_vector)}")
        
        results = await client.search(
            vectors=vectors,
            top=3
        )
        
        logger.info(f"Found {len(results)} results for vector search")
        
        # Print detailed results
        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Title: {result.get('page_title', 'N/A')} \"{result.get('section_title', 'N/A')}\"")
            logger.info(f"Content Type: {result.get('content_type', 'N/A')}")
            logger.info(f"Score: {result.get('@search.score', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error in Vector Search: {str(e)}")

async def test_text_vector_search():
    """Test text-based vector search."""
    try:
        client = AzureSearchClient()
        query = "I want to make hot chocolate with kit kat"
        logger.info(f"\nTesting text-based vector search with query: '{query}'")
        
        results = await client.search(
            text_query=query,
            top=3
        )
        
        logger.info(f"Found {len(results)} results for text-based vector search")
        
        # Print detailed results
        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Title: {result.get('page_title', 'N/A')} \"{result.get('section_title', 'N/A')}\"")
            logger.info(f"Content Type: {result.get('content_type', 'N/A')}")
            logger.info(f"Score: {result.get('@search.score', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error in Text-based Vector Search: {str(e)}")

async def test_hybrid_search():
    """Test hybrid search combining keyword and vector search."""
    try:
        client = AzureSearchClient()
        query = "what ingredients are in kit kat"
        logger.info(f"\nTesting hybrid search with query: '{query}' and content vector")
        
        # Generate random vector for testing
        content_vector = generate_test_vector()
        logger.info(f"Vector dimension: content={len(content_vector)}")
        
        results = await client.search(
            query=query,
            vectors={"content": content_vector},
            top=3
        )
        
        logger.info(f"Found {len(results)} results for hybrid search")
        
        # Print detailed results
        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Title: {result.get('page_title', 'N/A')} \"{result.get('section_title', 'N/A')}\"")
            logger.info(f"Content Type: {result.get('content_type', 'N/A')}")
            logger.info(f"Score: {result.get('@search.score', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error in Hybrid Search: {str(e)}")

async def test_filtered_search():
    """Test filtered search with content type and brand filters."""
    try:
        client = AzureSearchClient()
        query = "chocolate"
        filters = {
            "content_type": "brand",
            "brand": "BOOST",
            "keywords": ["calml"]
        }
        
        logger.info("\nTesting filtered search:")
        logger.info(f"Query: '{query}'")
        logger.info(f"Filters: {filters}")
        
        results = await client.search(
            query=query,
            content_type=filters["content_type"],
            brand=filters["brand"],
            keywords=filters["keywords"],
            top=3
        )
        
        logger.info(f"Found {len(results)} results for filtered search")
        
        # Print detailed results
        for i, result in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Title: {result.get('page_title', 'N/A')} \"{result.get('section_title', 'N/A')}\"")
            logger.info(f"Content Type: {result.get('content_type', 'N/A')}")
            logger.info(f"Brand: {result.get('brand', 'N/A')}")
            logger.info(f"Keywords: {result.get('keywords', [])}")
            logger.info(f"Score: {result.get('@search.score', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error in Filtered Search: {str(e)}")

async def run_test_scenarios():
    """Run all test scenarios."""
    test_scenarios = [
        ("Keyword Search", test_keyword_search),
        ("Vector Search", test_vector_search),
        ("Text-based Vector Search", test_text_vector_search),
        ("Hybrid Search", test_hybrid_search),
        ("Filtered Search", test_filtered_search)
    ]
    
    for scenario_name, test_func in test_scenarios:
        logger.info(f"\nRunning test scenario: {scenario_name}")
        logger.info("=" * 50)
        await test_func()
        logger.info(f"Test scenario completed: {scenario_name}")
        logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_test_scenarios()) 