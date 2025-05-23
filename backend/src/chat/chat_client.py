import logging
import sys
import os
from typing import Dict, List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv
from .session_manager import SessionManager

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
    Context-aware chat client that combines Azure AI Search with Azure OpenAI for 
    conversational search over Nestle content with conversation history management.
    """
    
    def __init__(self):
        """Initialize the chat client with search, OpenAI, and context/session management."""
        # Initialize search client with enhanced ranking
        self.search_client = AzureSearchClient(enable_enhanced_ranking=True)
        
        # Initialize session manager
        self.session_manager = SessionManager(session_timeout_hours=24)
        
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
    
    def _get_context_aware_prompt(self) -> str:
        """
        Get the prompt template for the LLM.
        
        Returns:
            str: The prompt template with placeholders for query, sources, and context
        """
        return """
        You are a helpful AI agent for Made with Nestlé website.
        Answer the query using only the sources provided below.
        Use bullets if the answer has multiple points.
        If the answer is longer than 3 sentences, provide a summary.
        Answer ONLY with the facts listed in the list of sources below.
        Cite your source when you answer the question.
        If there isn't enough information below, say you don't know.
        Do not generate answers that don't use the sources below.
        Focus on Nestle products, recipes, and brand information.
        Be helpful and friendly in your responses.
        
        Consider the conversation context when formulating your response.
        If this relates to previous questions in the conversation, acknowledge that context naturally.

        Conversation Context: {context_summary}
        
        Current Query: {query}
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
        session_id: Optional[str] = None,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_search_results: int = 5,
        use_vector_search: bool = True,
        use_context: bool = True
    ) -> Dict:
        """
        Perform context-aware search and generate a conversational response.
        
        This is the main RAG implementation with context awareness that:
        1. Manages conversation sessions and history
        2. Searches for relevant content using Azure AI Search with context enhancement
        3. Formats the results as sources with conversation context
        4. Sends to Azure OpenAI for answer generation with conversation history
        
        Args:
            query (str): User's question or search query
            session_id (Optional[str]): Conversation session ID (creates new if None)
            content_type (Optional[str]): Filter by content type (e.g., "recipe")
            brand (Optional[str]): Filter by brand (e.g., "Nestle")
            keywords (Optional[List[str]]): Filter by keywords
            top_search_results (int): Number of search results to use as context
            use_vector_search (bool): Whether to use vector search for better semantic matching
            use_context (bool): Whether to use conversation context for enhanced search
            
        Returns:
            Dict: Response containing answer, sources, metadata, and session info
        """
        try:
            logger.info(f"Processing context-aware chat query: {query}")
            
            # Get or create conversation session
            session = self.session_manager.get_or_create_session(session_id)
            
            # Add user message to conversation history
            session.add_user_message(query, {"use_vector_search": use_vector_search})
            
            # Prepare base search parameters
            search_params = {
                "query": query,
                "top": top_search_results,
                "content_type": content_type,
                "brand": brand,
                "keywords": keywords,
                "enable_ranking": True  # Use enhanced ranking
            }
            
            # Enhance search parameters with conversation context
            if use_context:
                enhanced_params = session.get_enhanced_search_params()
                
                # Apply context-based suggestions if not explicitly set
                if not content_type and enhanced_params.get("content_type"):
                    search_params["content_type"] = enhanced_params["content_type"]
                    logger.info(f"Applied context content type: {enhanced_params['content_type']}")
                
                if not brand and enhanced_params.get("suggested_brand"):
                    search_params["brand"] = enhanced_params["suggested_brand"]
                    logger.info(f"Applied context brand: {enhanced_params['suggested_brand']}")
                
                if not keywords and enhanced_params.get("suggested_keywords"):
                    search_params["keywords"] = enhanced_params["suggested_keywords"]
                    logger.info(f"Applied context keywords: {enhanced_params['suggested_keywords']}")
            
            # Add vector search if enabled
            if use_vector_search:
                search_params["text_query"] = query
            
            # Perform search to get grounding data
            search_results = await self.search_client.search(**search_params)
            
            if not search_results:
                no_results_response = {
                    "answer": "I couldn't find any relevant information about your question. Please try rephrasing your question or asking about something else.",
                    "sources": [],
                    "source_links": [],
                    "search_results_count": 0,
                    "query": query,
                    "session_id": session.session_id,
                    "conversation_context": session.get_conversation_summary(),
                    "filters_applied": {
                        "content_type": search_params.get("content_type"),
                        "brand": search_params.get("brand"),
                        "keywords": search_params.get("keywords")
                    }
                }
                
                # Add agent message to session
                session.add_agent_message(
                    no_results_response["answer"],
                    {"search_results_count": 0, "filters_applied": no_results_response["filters_applied"]}
                )
                
                return no_results_response
            
            # Format sources for LLM
            sources_formatted = self._format_search_results(search_results)
            
            # Format sources for frontend
            source_links = self._format_links(search_results)
            
            # Get conversation context summary
            context_summary = session.get_conversation_summary()
            
            # Prepare context-aware prompt with grounding data
            context_prompt = self._get_context_aware_prompt()
            full_prompt = context_prompt.format(
                query=query, 
                sources=sources_formatted,
                context_summary=context_summary
            )
            
            logger.info(f"Sending query to LLM with {len(search_results)} sources and conversation context")
            
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
                error_response = {
                    "answer": "I'm sorry, I couldn't generate a response. Please try again.",
                    "sources": search_results,
                    "source_links": source_links,
                    "search_results_count": len(search_results),
                    "query": query,
                    "session_id": session.session_id,
                    "conversation_context": context_summary,
                    "filters_applied": {
                        "content_type": search_params.get("content_type"),
                        "brand": search_params.get("brand"),
                        "keywords": search_params.get("keywords")
                    }
                }
                
                # Add agent message to session
                session.add_agent_message(
                    error_response["answer"],
                    {"error": "No choices in OpenAI response"}
                )
                
                return error_response
            
            answer = response.choices[0].message.content
            
            # Check if answer is empty
            if not answer:
                answer = "I found relevant sources but couldn't generate a complete answer. Please check the sources below."
            
            # Add agent message to conversation history
            session.add_agent_message(
                answer, 
                {
                    "search_results_count": len(search_results),
                    "filters_applied": {
                        "content_type": search_params.get("content_type"),
                        "brand": search_params.get("brand"),
                        "keywords": search_params.get("keywords")
                    },
                    "context_enhanced": use_context
                }
            )
            
            # Prepare response with context information
            return {
                "answer": answer,
                "sources": search_results,
                "source_links": source_links,
                "search_results_count": len(search_results),
                "query": query,
                "session_id": session.session_id,
                "conversation_context": context_summary,
                "context_enhanced_search": use_context,
                "filters_applied": {
                    "content_type": search_params.get("content_type"),
                    "brand": search_params.get("brand"),
                    "keywords": search_params.get("keywords")
                },
                "session_stats": {
                    "total_messages": len(session.messages),
                    "total_queries": session.metadata["total_queries"],
                    "total_responses": session.metadata["total_responses"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in context-aware search_and_chat: {str(e)}")
            
            # Try to get session for error response
            try:
                session = self.session_manager.get_or_create_session(session_id)
                session_info = {"session_id": session.session_id}
            except:
                session_info = {"session_id": None}
            
            return {
                "answer": "I'm sorry, I encountered an error while processing your question. Please try again.",
                "sources": [],
                "source_links": [],
                "search_results_count": 0,
                "query": query,
                "error": str(e),
                **session_info
            }
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            session_id (Optional[str]): Custom session ID, generates one if None
            
        Returns:
            str: Session ID
        """
        session = self.session_manager.create_session(session_id)
        return session.session_id
    
    def get_session_history(self, session_id: str) -> Optional[Dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Optional[Dict]: Session data or None if not found
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": len(session.messages),
            "messages": [msg.to_dict() for msg in session.messages],
            "conversation_summary": session.get_conversation_summary(),
            "search_context": session.search_context.to_dict(),
            "metadata": session.metadata
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.
        
        Args:
            session_id (str): Session ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        return self.session_manager.delete_session(session_id)
    
    def get_all_sessions_stats(self) -> Dict:
        """
        Get statistics about all active sessions.
        
        Returns:
            Dict: Session statistics
        """
        return self.session_manager.get_session_stats()
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        return self.session_manager.cleanup_expired_sessions()
    
    async def get_recipe(self, ingredient: str, session_id: Optional[str] = None) -> Dict:
        """
        Get recipe suggestions for a specific ingredient with conversation context.
        
        Args:
            ingredient (str): Ingredient to search for
            session_id (Optional[str]): Session ID for context
            
        Returns:
            Dict: Recipe suggestions with answers
        """
        query = f"recipes with {ingredient}"
        return await self.search_and_chat(
            query=query,
            session_id=session_id,
            content_type="recipe",
            top_search_results=5,
            use_vector_search=True,
            use_context=True
        )
    
    async def get_product(self, product_name: str, session_id: Optional[str] = None) -> Dict:
        """
        Get information about a specific Nestle product with conversation context.
        
        Args:
            product_name (str): Name of the product
            session_id (Optional[str]): Session ID for context
            
        Returns:
            Dict: Product information with answers
        """
        query = f"tell me about {product_name}"
        return await self.search_and_chat(
            query=query,
            session_id=session_id,
            content_type="brand",
            keywords=[f"{product_name}"],
            top_search_results=5,
            use_vector_search=True,
            use_context=True
        )
    
    async def get_cooking_tips(self, topic: str, session_id: Optional[str] = None) -> Dict:
        """
        Get cooking tips and advice with conversation context.
        
        Args:
            topic (str): Cooking topic or technique
            session_id (Optional[str]): Session ID for context
            
        Returns:
            Dict: Cooking tips with answers
        """
        query = f"cooking tips for {topic}"
        return await self.search_and_chat(
            query=query,
            session_id=session_id,
            keywords=["cooking", "tips", "baking"],
            top_search_results=5,
            use_vector_search=True,
            use_context=True
        )
    
    async def ask_about_nutrition(self, food_item: str, session_id: Optional[str] = None) -> Dict:
        """
        Get nutritional information about a food item or Nestle product with conversation context.
        
        Args:
            food_item (str): Food item or product name
            session_id (Optional[str]): Session ID for context
            
        Returns:
            Dict: Nutritional information with answers
        """
        query = f"nutrition information for {food_item}"
        return await self.search_and_chat(
            query=query,
            session_id=session_id,
            keywords=["nutrition", "calories"],
            top_search_results=5,
            use_vector_search=True,
            use_context=True
        ) 