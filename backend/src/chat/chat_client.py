import logging
import sys
import os
from typing import Dict, List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

# Add the search module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "search"))
from search_client import AzureSearchClient

# Load environment variables
load_dotenv()

# Azure OpenAI API settings.
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class NestleChatClient:
    """
    Chat client that combines Azure AI Search with Azure OpenAI for 
    conversational search over Nestle content.
    """
    
    def __init__(self):
        """Initialize the chat client with search and OpenAI clients."""
        # Initialize search client
        self.search_client = AzureSearchClient()
        
        # Store deployment name
        self.deployment_name = AZURE_OPENAI_DEPLOYMENT
        
        # Initialize Azure OpenAI client
        try:
            self.openai_client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                azure_endpoint=AZURE_OPENAI_ENDPOINT,
                api_version=AZURE_OPENAI_API_VERSION
            )
            logger.info("Successfully initialized chat client")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    def _get_grounded_prompt(self) -> str:
        """
        Get the grounded prompt template for the LLM.
        
        Returns:
            str: The prompt template with placeholders for query and sources
        """
        return """
        You are a helpful AI assistant for Made with Nestlé website.
        Answer the query using only the sources provided below.
        Use bullets if the answer has multiple points.
        If the answer is longer than 3 sentences, provide a summary.
        Answer ONLY with the facts listed in the list of sources below.
        Cite your source when you answer the question.
        If there isn't enough information below, say you don't know.
        Do not generate answers that don't use the sources below.
        Focus on Nestle products, recipes, and brand information.
        Be helpful and friendly in your responses.

        Query: {query}
        Sources:
        {sources}
        """
    
    def _format_links(self, search_results: List[Dict]) -> List[Dict]:
        """
        Format search results as source links for frontend display.
        
        Args:
            search_results (List[Dict]): Search results from Azure Search
            
        Returns:
            List[Dict]: Formatted source links for frontend
        """
        if not search_results:
            return []
        
        formatted_links = []
        for i, result in enumerate(search_results, 1):
            try:
                # Safely extract URL parts
                url = result.get("url", "")
                domain = ""
                if url and "/" in url:
                    try:
                        domain = url.split("/")[2] if len(url.split("/")) > 2 else ""
                    except (IndexError, AttributeError):
                        domain = ""
                
                # Safely extract content
                content = result.get("content", "")
                snippet = content[:150] + "..." if len(content) > 150 else content
                
                source_link = {
                    "id": i,
                    "title": result.get("page_title", "Unknown Source"),
                    "section": result.get("section_title", ""),
                    "url": url,
                    "snippet": snippet,
                    "domain": domain
                }
                formatted_links.append(source_link)
            except Exception as e:
                logger.warning(f"Error formatting source link {i}: {str(e)}")
                # Add a basic link even if formatting fails
                formatted_links.append({
                    "id": i,
                    "title": "Source",
                    "section": "",
                    "url": result.get("url", ""),
                    "snippet": "Content preview unavailable",
                    "domain": ""
                })
        
        return formatted_links
    
    def _format_search_results(self, search_results: List[Dict]) -> str:
        """
        Format search results as sources for the LLM.
        Uses a unique separator to make the sources distinct.
        
        Args:
            search_results (List[Dict]): Search results from Azure Search
            
        Returns:
            str: Formatted sources string
        """
        if not search_results:
            return "No relevant sources found."
        
        formatted_sources = []
        for i, result in enumerate(search_results, 1):
            source = f"Source {i}:\n"
            source += f"Title: {result.get('page_title', 'Unknown')}\n"
            source += f"Section: {result.get('section_title', 'Unknown')}\n"
            source += f"Content: {result.get('content', 'No content')}\n"
            if result.get('url'):
                source += f"Link: {result.get('url')}\n"
            formatted_sources.append(source)
        
        # Use repeated equal signs as separator (unlikely to appear in content)
        return "\n=================\n".join(formatted_sources)
    
    async def search_and_chat(
        self,
        query: str,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_search_results: int = 5,
        use_vector_search: bool = True
    ) -> Dict:
        """
        Perform search and generate a conversational response.
        
        This is the main RAG implementation that:
        1. Searches for relevant content using Azure AI Search
        2. Formats the results as sources
        3. Sends to Azure OpenAI for answer generation
        
        Args:
            query (str): User's question or search query
            content_type (Optional[str]): Filter by content type (e.g., "recipe")
            brand (Optional[str]): Filter by brand (e.g., "Nestle")
            keywords (Optional[List[str]]): Filter by keywords
            top_search_results (int): Number of search results to use as context
            use_vector_search (bool): Whether to use vector search for better semantic matching
            
        Returns:
            Dict: Response containing answer, sources, and metadata
        """
        try:
            logger.info(f"Processing chat query: {query}")
            
            # Prepare search parameters
            search_params = {
                "query": query,
                "top": top_search_results,
                "content_type": content_type,
                "brand": brand,
                "keywords": keywords
            }
            
            # Add vector search if enabled
            if use_vector_search:
                search_params["text_query"] = query
            
            # Perform search to get grounding data
            search_results = await self.search_client.search(**search_params)
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant information about your question. Please try rephrasing your question or asking about something else.",
                    "sources": [],
                    "source_links": [],
                    "search_results_count": 0,
                    "query": query,
                    "filters_applied": {
                        "content_type": content_type,
                        "brand": brand,
                        "keywords": keywords
                    }
                }
            
            # Format sources for LLM
            sources_formatted = self._format_search_results(search_results)
            
            # Format sources for frontend
            source_links = self._format_links(search_results)
            
            # Prepare prompt with grounding data
            grounded_prompt = self._get_grounded_prompt()
            full_prompt = grounded_prompt.format(query=query, sources=sources_formatted)
            
            logger.info(f"Sending query to LLM with {len(search_results)} sources")
            
            # Only call OpenAI if deployment name is configured
            if not self.deployment_name:
                return {
                    "answer": f"Based on {len(search_results)} sources found, but AI response generation is not configured.",
                    "sources": search_results,
                    "source_links": source_links,
                    "search_results_count": len(search_results),
                    "query": query,
                    "filters_applied": {
                        "content_type": content_type,
                        "brand": brand,
                        "keywords": keywords
                    }
                }
            
            # Generate response from LLM
            response = self.openai_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                model=self.deployment_name,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Safely extract answer from response
            if not response.choices or len(response.choices) == 0:
                logger.error("OpenAI response contains no choices")
                return {
                    "answer": "I'm sorry, I couldn't generate a response. Please try again.",
                    "sources": search_results,
                    "source_links": source_links,
                    "search_results_count": len(search_results),
                    "query": query,
                    "filters_applied": {
                        "content_type": content_type,
                        "brand": brand,
                        "keywords": keywords
                    }
                }
            
            answer = response.choices[0].message.content
            
            # Check if answer is empty
            if not answer:
                answer = "I found relevant sources but couldn't generate a complete answer. Please check the sources below."
            
            # Prepare response
            return {
                "answer": answer,
                "sources": search_results,
                "source_links": source_links,
                "search_results_count": len(search_results),
                "query": query,
                "filters_applied": {
                    "content_type": content_type,
                    "brand": brand,
                    "keywords": keywords
                }
            }
            
        except Exception as e:
            logger.error(f"Error in search_and_chat: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "sources": [],
                "source_links": [],
                "search_results_count": 0,
                "query": query,
                "error": str(e)
            }
    
    async def get_recipe(self, ingredient: str) -> Dict:
        """
        Get recipe suggestions for a specific ingredient.
        
        Args:
            ingredient (str): Ingredient to search for
            
        Returns:
            Dict: Recipe suggestions with answers
        """
        query = f"recipes with {ingredient}"
        return await self.search_and_chat(
            query=query,
            content_type="recipe",
            top_search_results=5,
            use_vector_search=True
        )
    
    async def get_product(self, product_name: str) -> Dict:
        """
        Get information about a specific Nestle product.
        
        Args:
            product_name (str): Name of the product
            
        Returns:
            Dict: Product information with answers
        """
        query = f"tell me about {product_name}"
        return await self.search_and_chat(
            query=query,
            content_type="brand",
            keywords=[f"{product_name}"],
            top_search_results=5,
            use_vector_search=True
        )
    
    async def get_cooking_tips(self, topic: str) -> Dict:
        """
        Get cooking tips and advice.
        
        Args:
            topic (str): Cooking topic or technique
            
        Returns:
            Dict: Cooking tips with answers
        """
        query = f"cooking tips for {topic}"
        return await self.search_and_chat(
            query=query,
            keywords=["cooking", "tips", "baking"],
            top_search_results=5,
            use_vector_search=True
        )
    
    async def ask_about_nutrition(self, food_item: str) -> Dict:
        """
        Get nutritional information about a food item or Nestle product.
        
        Args:
            food_item (str): Food item or product name
            
        Returns:
            Dict: Nutritional information with answers
        """
        query = f"nutrition information for {food_item}"
        return await self.search_and_chat(
            query=query,
            keywords=["nutrition", "calories"],
            top_search_results=5,
            use_vector_search=True
        ) 