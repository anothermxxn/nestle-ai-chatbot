import logging
from typing import Dict, List, Optional
from openai import AzureOpenAI

try:
    from backend.src.chat.session_manager import SessionManager
    from backend.src.search.search_client import AzureSearchClient
    from backend.src.search.graphrag_client import GraphRAGClient
    from backend.src.chat.graphrag_formatter import GraphRAGFormatter
except ImportError:
    from src.chat.session_manager import SessionManager
    from src.search.search_client import AzureSearchClient
    from src.search.graphrag_client import GraphRAGClient
    from src.chat.graphrag_formatter import GraphRAGFormatter

# Dynamic import to handle both local development and Docker environments
try:
    from backend.config import (
        AZURE_OPENAI_CONFIG,
        CHAT_CONFIG,
        CHAT_PROMPTS,
        validate_azure_openai_config
    )
except ImportError:
    from config import (
        AZURE_OPENAI_CONFIG,
        CHAT_CONFIG,
        CHAT_PROMPTS,
        validate_azure_openai_config
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class NestleChatClient:
    """
    Chat client that combines Azure AI Search, Azure Cosmos DB with Azure OpenAI for 
    conversational search over Nestle content.
    """
    
    def __init__(self):
        """Initialize the chat client."""
        if not validate_azure_openai_config():
            raise ValueError("Invalid Azure OpenAI configuration")
        
        self.search_client = AzureSearchClient(enable_enhanced_ranking=True)
        
        try:
            self.graphrag_client = GraphRAGClient()
            self.graphrag_formatter = GraphRAGFormatter()
            logger.info("GraphRAG components initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize GraphRAG components: {str(e)}")
            self.graphrag_client = None
            self.graphrag_formatter = None
        
        self.session_manager = SessionManager(
            session_timeout_hours=CHAT_CONFIG["session_timeout_hours"]
        )
        
        self.deployment_name = AZURE_OPENAI_CONFIG["deployment"]
        
        try:
            self.openai_client = AzureOpenAI(
                api_key=AZURE_OPENAI_CONFIG["api_key"],
                azure_endpoint=AZURE_OPENAI_CONFIG["endpoint"],
                api_version=AZURE_OPENAI_CONFIG["api_version"]
            )
            logger.info("Successfully initialized chat client")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison to handle edge cases.
        
        Args:
            url (str): Raw URL
            
        Returns:
            str: Normalized URL for comparison
        """
        if not url:
            return ""
        
        # Convert to lowercase
        normalized = url.lower().strip()
        
        # Remove protocol differences (http vs https)
        normalized = normalized.replace("https://", "").replace("http://", "")
        
        # Remove www prefix
        if normalized.startswith("www."):
            normalized = normalized[4:]
        
        # Remove trailing slash
        if normalized.endswith("/"):
            normalized = normalized[:-1]
        
        # Remove common query parameters that don't affect content
        if "?" in normalized:
            base_url, query = normalized.split("?", 1)
            # Keep only meaningful query parameters, remove tracking/session params
            meaningful_params = []
            for param in query.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    # Skip common tracking/session parameters
                    if key not in ["utm_source", "utm_medium", "utm_campaign", "sessionid", "sid", "_ga", "fbclid"]:
                        meaningful_params.append(param)
            
            if meaningful_params:
                normalized = base_url + "?" + "&".join(meaningful_params)
            else:
                normalized = base_url
        
        # Remove fragment identifiers
        if "#" in normalized:
            normalized = normalized.split("#")[0]
        
        return normalized

    async def _check_domain_and_respond(self, query: str, session, search_params: Dict) -> Dict:
        """
        Check if query is within knowledge domain and provide appropriate response.
        
        Args:
            query (str): User query
            session: Session object
            search_params (Dict): Search parameters used
            
        Returns:
            Dict: Either None (proceed with search) or response dict (out of domain)
        """
        try:
            # Use LLM to classify the query and potentially respond
            prompt = CHAT_PROMPTS["domain_classification_prompt"].format(query=query)
            
            response_text = self.openai_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.deployment_name,
                temperature=0.7,
                max_tokens=200
            )
            
            if response_text.choices and len(response_text.choices) > 0:
                llm_response = response_text.choices[0].message.content.strip()
                
                # If LLM says it's within domain, return None to proceed with search
                if "DOMAIN_MATCH" in llm_response:
                    return None
                
                # Otherwise, use the LLM's response as the out-of-domain response
                response = {
                    "answer": llm_response,
                    "sources": [],
                    "search_results_count": 0,
                    "query": query,
                    "filters_applied": {
                        "content_type": search_params.get("content_type"),
                        "brand": search_params.get("brand"),
                        "keywords": search_params.get("keywords")
                    },
                    "graphrag_enhanced": False,
                    "combined_relevance_score": 0.0,
                    "retrieval_metadata": {}
                }
                
                session.add_assistant_message(
                    response["answer"],
                    {"search_results_count": 0, "filters_applied": response["filters_applied"], "out_of_domain": True}
                )
                
                return response
            else:
                # If LLM call fails, proceed with search (safe fallback)
                return None
                
        except Exception as e:
            logger.warning(f"Failed to classify query domain: {str(e)}")
            # If classification fails, proceed with search (safe fallback)
            return None

    def _format_links(self, search_results: List[Dict]) -> List[Dict]:
        """
        Format search results as source links for frontend display.
        Removes duplicate URLs to ensure unique sources.
        
        Args:
            search_results (List[Dict]): Search results from Azure Search
            
        Returns:
            List[Dict]: Formatted source links for frontend with unique URLs
        """
        if not search_results:
            return []
        
        formatted_links = []
        seen_urls = set()
        link_id = 1
        
        for result in search_results:
            try:
                # Safely extract URL parts
                url = result.get("url", "")
                
                # Skip if URL is empty
                if not url:
                    continue
                
                # Normalize URL for comparison
                normalized_url = self._normalize_url(url)
                
                # Skip if normalized URL already seen
                if normalized_url in seen_urls:
                    logger.debug(f"Skipping duplicate URL: {url} (normalized: {normalized_url})")
                    continue
                
                seen_urls.add(normalized_url)
                
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
                    "id": link_id,
                    "title": result.get("page_title", "Unknown Source"),
                    "section": result.get("section_title", ""),
                    "url": url,  # Keep original URL for display
                    "snippet": snippet,
                    "domain": domain
                }
                formatted_links.append(source_link)
                link_id += 1
                
            except Exception as e:
                logger.warning(f"Error formatting source link: {str(e)}")
                # Add a basic link even if formatting fails (if URL is unique)
                url = result.get("url", "")
                if url:
                    normalized_url = self._normalize_url(url)
                    if normalized_url and normalized_url not in seen_urls:
                        seen_urls.add(normalized_url)
                        formatted_links.append({
                            "id": link_id,
                            "title": "Source",
                            "section": "",
                            "url": url,
                            "snippet": "Content preview unavailable",
                            "domain": ""
                        })
                        link_id += 1
        
        logger.info(f"Deduplicated sources: {len(search_results)} -> {len(formatted_links)} unique URLs")
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
        
        return "\n=================\n".join(formatted_sources)
    
    def _prepare_search_params(self, query: str, session, content_type: Optional[str], 
                              brand: Optional[str], keywords: Optional[List[str]], 
                              top_search_results: int) -> Dict:
        """
        Prepare search parameters with context enhancement.
        
        Args:
            query (str): Search query
            session: Session object for context
            content_type (Optional[str]): Content type filter
            brand (Optional[str]): Brand filter
            keywords (Optional[List[str]]): Keywords filter
            top_search_results (int): Number of results
            
        Returns:
            Dict: Enhanced search parameters
        """
        search_params = {
            "query": query,
            "top": top_search_results,
            "content_type": content_type,
            "brand": brand,
            "keywords": keywords,
            "enable_ranking": True,
            "text_query": query
        }
        
        enhanced_params = session.get_enhanced_search_params()
        
        if not content_type and enhanced_params.get("content_type"):
            search_params["content_type"] = enhanced_params["content_type"]
            logger.info(f"Applied context content type: {enhanced_params['content_type']}")
        
        if not brand and enhanced_params.get("suggested_brand"):
            search_params["brand"] = enhanced_params["suggested_brand"]
            logger.info(f"Applied context brand: {enhanced_params['suggested_brand']}")
        
        if not keywords and enhanced_params.get("suggested_keywords"):
            search_params["keywords"] = enhanced_params["suggested_keywords"]
            logger.info(f"Applied context keywords: {enhanced_params['suggested_keywords']}")
        
        return search_params

    async def _perform_search(self, query: str, search_params: Dict, top_search_results: int):
        """
        Perform search using GraphRAG or fallback to regular search.
        
        Args:
            query (str): Search query
            search_params (Dict): Search parameters
            top_search_results (int): Number of results
            
        Returns:
            Tuple[List[Dict], Optional[GraphContext]]: Search results and graph context
        """
        if self.graphrag_client and self.graphrag_formatter:
            logger.info("Using GraphRAG for enhanced context retrieval")
            graphrag_result = await self.graphrag_client.hybrid_search(
                query=query,
                content_type=search_params.get("content_type"),
                brand=search_params.get("brand"),
                keywords=search_params.get("keywords"),
                top_results=top_search_results,
                graph_expansion_depth=1
            )
            search_results = graphrag_result.vector_results
            graph_context = self.graphrag_formatter.format_graphrag_context(graphrag_result, query)
            return search_results, graph_context
        else:
            logger.warning("GraphRAG components not available, falling back to regular vector search")
            search_results = await self.search_client.search(**search_params)
            return search_results, None

    def _create_no_results_response(self, query: str, session, search_params: Dict) -> Dict:
        """
        Create response when no search results are found.
        
        Args:
            query (str): Original query
            session: Session object
            search_params (Dict): Search parameters used
            
        Returns:
            Dict: No results response
        """
        response = {
            "answer": CHAT_PROMPTS["no_results_message"],
            "sources": [],
            "search_results_count": 0,
            "query": query,
            "filters_applied": {
                "content_type": search_params.get("content_type"),
                "brand": search_params.get("brand"),
                "keywords": search_params.get("keywords")
            },
            "graphrag_enhanced": False,
            "combined_relevance_score": 0.0,
            "retrieval_metadata": {}
        }
        
        session.add_assistant_message(
            response["answer"],
            {"search_results_count": 0, "filters_applied": response["filters_applied"]}
        )
        
        return response

    def _create_prompt(self, query: str, search_results: List[Dict], graph_context, conversation_history) -> str:
        """
        Create the prompt for the LLM based on search results, graph context, and conversation history.
        
        Args:
            query (str): User query
            search_results (List[Dict]): Search results
            graph_context: Graph context object or None
            conversation_history: List of previous messages for context
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Format conversation context
        conversation_context = ""
        
        if conversation_history:
            conversation_context = "\n\nCONVERSATION HISTORY:\n"
            for msg in conversation_history:
                role = "User" if msg.role == "user" else "Assistant"
                conversation_context += f"{role}: {msg.content}\n"
            conversation_context += f"\nCurrent question: {query}\n"
        
        if graph_context:
            if conversation_context:
                # Create a modified system prompt template that includes conversation context
                modified_system_prompt = CHAT_PROMPTS["system_prompt"].replace(
                    "USER QUESTION: {query}",
                    f"{conversation_context}\nUSER QUESTION: {{query}}"
                )
            else:
                modified_system_prompt = CHAT_PROMPTS["system_prompt"]
            
            # Create the graph enhanced prompt with the modified template
            final_prompt = self.graphrag_formatter.create_graph_enhanced_prompt(
                query, graph_context, modified_system_prompt
            )
            
            return final_prompt
        else:
            sources_formatted = self._format_search_results(search_results)
            prompt_template = CHAT_PROMPTS["system_prompt"]
            
            if conversation_context:
                # Insert conversation context before the current question
                prompt_template = prompt_template.replace(
                    "USER QUESTION: {query}",
                    f"{conversation_context}\nUSER QUESTION: {{query}}"
                )
            
            final_prompt = prompt_template.format(
                query=query, 
                sources=sources_formatted,
                graph_context="No graph context available."
            )
            
            return final_prompt

    async def _generate_llm_response(self, prompt: str) -> str:
        """
        Generate response from the LLM.
        
        Args:
            prompt (str): Formatted prompt
            
        Returns:
            str: Generated answer
        """
        response = self.openai_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.deployment_name,
            temperature=CHAT_CONFIG["default_temperature"],
            max_tokens=CHAT_CONFIG["default_max_tokens"]
        )
        
        if not response.choices or len(response.choices) == 0:
            raise Exception("No choices in OpenAI response")
        
        answer = response.choices[0].message.content
        return answer if answer else CHAT_PROMPTS["generation_error_message"]

    def _create_final_response(self, answer: str, search_results: List[Dict], 
                              source_links: List[Dict], query: str, session, 
                              search_params: Dict, graph_context) -> Dict:
        """
        Create the final response with all metadata.
        
        Args:
            answer (str): Generated answer
            search_results (List[Dict]): Search results
            source_links (List[Dict]): Formatted source links
            query (str): Original query
            session: Session object
            search_params (Dict): Search parameters
            graph_context: Graph context object or None
            
        Returns:
            Dict: Complete response
        """
        context_summary = session.get_conversation_summary()
        
        base_response = {
            "answer": answer,
            "sources": search_results,
            "source_links": source_links,
            "search_results_count": len(search_results),
            "query": query,
            "session_id": session.session_id,
            "conversation_context": context_summary,
            "context_enhanced_search": True,
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
        
        if graph_context:
            enhanced_response = self.graphrag_formatter.format_relationship_aware_response(
                answer, graph_context
            )
            
            session.add_assistant_message(answer, {
                "search_results_count": len(search_results),
                "filters_applied": base_response["filters_applied"],
                "context_enhanced": True,
                "graphrag_enhanced": True,
                "entities_referenced": enhanced_response.get("entities_referenced", 0),
                "relationships_used": enhanced_response.get("relationships_used", 0)
            })
            
            base_response.update({
                "graphrag_enhanced": True,
                "combined_relevance_score": enhanced_response.get("combined_relevance_score", 0.0),
                "retrieval_metadata": enhanced_response.get("retrieval_metadata", {})
            })
        else:
            session.add_assistant_message(answer, {
                "search_results_count": len(search_results),
                "filters_applied": base_response["filters_applied"],
                "context_enhanced": True,
                "graphrag_enhanced": False,
                "graphrag_fallback": True
            })
            
            base_response.update({
                "graphrag_enhanced": False,
                "graphrag_fallback": True
            })
        
        return base_response

    async def search_and_chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_search_results: int = 5
    ) -> Dict:
        """
        Perform context-aware search and generate a conversational response.
        
        Args:
            query (str): User's question or search query
            session_id (Optional[str]): Conversation session ID (creates new if None)
            content_type (Optional[str]): Filter by content type (e.g., "recipe")
            brand (Optional[str]): Filter by brand (e.g., "Nestle")
            keywords (Optional[List[str]]): Filter by keywords
            top_search_results (int): Number of search results to use as context
            
        Returns:
            Dict: Response containing answer, sources, metadata, and session info
        """
        try:
            logger.info(f"Processing context-aware chat query: {query}")
            
            session = self.session_manager.get_or_create_session(session_id)
            
            # Check if this is within the chatbot's knowledge domain
            search_params = self._prepare_search_params(
                query, session, content_type, brand, keywords, top_search_results
            )
            
            domain_response = await self._check_domain_and_respond(query, session, search_params)
            if domain_response:
                return domain_response
            
            # Get conversation context
            conversation_history = []
            if len(session.messages) > 0:
                recent_messages = session.get_context_messages()
                conversation_history = recent_messages[-4:]  # Last 4 messages for context
            
            # Add the current user message
            session.add_user_message(query, {"vector_search_enabled": True, "context_enabled": True})
            
            # Perform search
            search_results, graph_context = await self._perform_search(
                query, search_params, top_search_results
            )
            
            # Handle results
            if not search_results:
                return self._create_no_results_response(query, session, search_params)
            prompt = self._create_prompt(query, search_results, graph_context, conversation_history)
            source_links = self._format_links(search_results)
            
            # Create final response
            answer = await self._generate_llm_response(prompt)
            return self._create_final_response(
                answer, search_results, source_links, query, session, search_params, graph_context
            )
            
        except Exception as e:
            logger.error(f"Error in context-aware search_and_chat: {str(e)}")
            
            try:
                session = self.session_manager.get_or_create_session(session_id)
                session_info = {"session_id": session.session_id}
            except:
                session_info = {"session_id": None}
            
            return {
                "answer": CHAT_PROMPTS["error_message"],
                "sources": [],
                "search_results_count": 0,
                "query": query,
                "filters_applied": {
                    "content_type": content_type,
                    "brand": brand,
                    "keywords": keywords
                },
                "graphrag_enhanced": False,
                "combined_relevance_score": 0.0,
                "retrieval_metadata": {},
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
            top_search_results=5
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
            top_search_results=5
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
            top_search_results=5
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
            top_search_results=5
        ) 