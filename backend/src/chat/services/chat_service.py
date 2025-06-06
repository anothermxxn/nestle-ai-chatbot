import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from openai import AzureOpenAI

if TYPE_CHECKING:
    from .session_service import ConversationMessage
    from .context_service import SearchContext, ContextExtractor

try:
    from backend.src.search.services.azure_search import AzureSearchClient
    from backend.src.search.services.graphrag import GraphRAGClient
    from backend.src.chat.formatters.graphrag_formatter import GraphRAGFormatter
    from backend.src.chat.services.context_service import SearchContext, ContextExtractor
except ImportError:
    from src.search.services.azure_search import AzureSearchClient
    from src.search.services.graphrag import GraphRAGClient
    from src.chat.formatters.graphrag_formatter import GraphRAGFormatter
    from src.chat.services.context_service import SearchContext, ContextExtractor

# Dynamic import to handle both local development and Docker environments
try:
    from backend.config import (
        AZURE_OPENAI_CONFIG,
        CHAT_CONFIG,
        CHAT_PROMPTS,
        DOMAIN_CHECK_CONFIG,
    )
except ImportError:
    from config import (
        AZURE_OPENAI_CONFIG,
        CHAT_CONFIG,
        CHAT_PROMPTS,
        DOMAIN_CHECK_CONFIG,
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
        """Initialize the Nestle Chat Client."""
        # Initialize Azure AI Search client
        self.search_client = AzureSearchClient()
        
        # Initialize GraphRAG client for hybrid search
        self.graphrag_client = GraphRAGClient()
        
        # Initialize GraphRAG component for enhanced context
        self.graphrag_formatter = GraphRAGFormatter()
        
        
        # Initialize Azure OpenAI client
        self.openai_client = AzureOpenAI(
            api_key=AZURE_OPENAI_CONFIG["api_key"],
            azure_endpoint=AZURE_OPENAI_CONFIG["endpoint"],
            api_version=AZURE_OPENAI_CONFIG["api_version"]
        )
        
        # Store deployment name for LLM calls
        self.deployment_name = AZURE_OPENAI_CONFIG["deployment"]
        
        logger.info("NestleChatClient initialized successfully")

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
    
    async def _perform_search(self, search_params: Dict, top_search_results: int):
        """
        Perform hybrid search using both vector search and GraphRAG.
        
        Args:
            search_params (Dict): Search parameters including query and filters
            top_search_results (int): Number of results
            
        Returns:
            Tuple[List[Dict], GraphRAGResult]: Search results and graph context
        """
        try:
            logger.info("Using hybrid search")
            graphrag_result = await self.graphrag_client.hybrid_search(
                query=search_params.get("query"),
                top_results=top_search_results,
                content_type=search_params.get("content_type"),
                brand=search_params.get("brand"),
                keywords=search_params.get("keywords")
            )
            
            if graphrag_result and graphrag_result.vector_results:
                logger.info(f"GraphRAG returned {len(graphrag_result.vector_results)} results")
                return graphrag_result.vector_results, graphrag_result
            else:
                logger.info("GraphRAG returned no results, falling back to vector search")
                
        except Exception as e:
            logger.warning(f"GraphRAG search failed: {str(e)}, falling back to vector search")
        
        # Fallback to vector search
        logger.info("Using vector search")
        search_results = await self.search_client.search(
            query=search_params.get("query"),
            top=top_search_results,
            content_type=search_params.get("content_type"),
            brand=search_params.get("brand"),
            keywords=search_params.get("keywords")
        )
        return search_results, None

    def _create_prompt(self, query: str, search_results: List[Dict], graphrag_result, conversation_history) -> str:
        """
        Create the prompt for the LLM based on search results, graph context, and conversation history.
        
        Args:
            query (str): User query
            search_results (List[Dict]): Search results
            graphrag_result: GraphRAGResult object or None
            conversation_history: List of previous messages for context
            
        Returns:
            str: Formatted prompt for LLM
        """
        prompt_template = CHAT_PROMPTS["system_prompt"]
        
        # Format conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nCONVERSATION HISTORY:\n"
            for msg in conversation_history:
                role = "User" if msg.role == "user" else "Assistant"
                conversation_context += f"{role}: {msg.content}\n"
            conversation_context += f"\nCurrent question: {query}\n"
        if conversation_context:
            prompt_template = prompt_template.replace(
                "USER QUESTION: {query}",
                conversation_context
            )
        
        if graphrag_result:
            try:
                final_prompt = self.graphrag_formatter.create_graph_enhanced_prompt(
                    query, graphrag_result, prompt_template
                )
                
                return final_prompt
                
            except Exception as e:
                logger.error(f"Failed to create graph-enhanced prompt: {str(e)}")
        
        # Fallback to regular sources formatting
        sources_formatted = self._format_search_results(search_results)
        
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

    async def search_and_chat(
        self,
        query: str,
        conversation_history: Optional[List['ConversationMessage']] = None,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_search_results: int = 5
    ) -> Dict:
        """
        Perform context-aware search and generate a conversational response.
        
        Args:
            query (str): User's question or search query
            conversation_history (Optional[List['ConversationMessage']]): Previous conversation messages as ConversationMessage objects
            content_type (Optional[str]): Filter by content type (e.g., "recipe")
            brand (Optional[str]): Filter by brand (e.g., "Nestle")
            keywords (Optional[List[str]]): Filter by keywords
            top_search_results (int): Number of search results to use as context
            
        Returns:
            Dict: Response containing answer, sources, metadata
        """
        try:
            logger.info(f"Processing chat query: {query}")
            
            # Extract search context from conversation history
            search_context = self._extract_search_context_from_history(conversation_history)
            
            # Check if this is within the chatbot's knowledge domain
            search_params = self._prepare_search_params(
                query, search_context, content_type, brand, keywords, top_search_results
            )
            
            domain_response = await self._check_domain_and_respond(query, search_params)
            if domain_response:
                return domain_response
            
            # Convert conversation history to ChatMessage format for prompt creation
            formatted_conversation_history = self._format_conversation_history(conversation_history)
            
            # Perform search
            search_results, graphrag_result = await self._perform_search(
                search_params, top_search_results
            )
            
            # Handle results
            if not search_results:
                return self._create_no_results_response(query, search_params)
            
            prompt = self._create_prompt(query, search_results, graphrag_result, formatted_conversation_history)
            source_links = self._format_links(search_results)
            
            # Create final response
            answer = await self._generate_llm_response(prompt)
            return self._create_final_response(
                answer, search_results, source_links, query, search_params, graphrag_result
            )
            
        except Exception as e:
            logger.error(f"Error in context-aware search_and_chat: {str(e)}")
            
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
                "error": str(e)
            }
    
    def _extract_search_context_from_history(self, conversation_history: Optional[List['ConversationMessage']]) -> 'SearchContext':
        """
        Extract search context from conversation history.
        
        Args:
            conversation_history (Optional[List['ConversationMessage']]): Previous conversation messages as ConversationMessage objects
            
        Returns:
            SearchContext: Extracted search context
        """
        search_context = SearchContext(
            recent_topics=[],
            preferred_content_types=[],
            mentioned_brands=[],
            mentioned_products=[],
            conversation_themes=[]
        )
        
        if not conversation_history:
            return search_context
        
        context_extractor = ContextExtractor()
        
        # Process recent conversation messages
        recent_messages = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
        
        for msg in recent_messages:
            # Only process user messages for context
            if msg.role == 'user':
                context_extractor.update_search_context(msg.content, search_context)
        
        return search_context
    
    def _format_conversation_history(self, conversation_history: Optional[List['ConversationMessage']]):
        """
        Convert conversation history to ChatMessage format.
        
        Args:
            conversation_history (Optional[List['ConversationMessage']]): ConversationMessage objects
            
        Returns:
            List: Formatted conversation history for prompt creation
        """
        if not conversation_history:
            return []
        
        from .context_service import ChatMessage
        
        formatted_history = []
        # Use recent messages for context
        recent_messages = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
        
        for msg in recent_messages:
            try:
                chat_msg = ChatMessage(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    metadata=msg.metadata
                )
                formatted_history.append(chat_msg)
            except Exception as e:
                logger.warning(f"Failed to format conversation message: {e}")
                continue
        
        return formatted_history
    
    def _prepare_search_params(self, query: str, search_context: 'SearchContext', 
                               content_type: Optional[str], brand: Optional[str], 
                               keywords: Optional[List[str]], top_search_results: int) -> Dict:
        """
        Prepare search parameters using context extraction.
        
        Args:
            query (str): User query
            search_context (SearchContext): Extracted search context
            content_type (Optional[str]): Content type filter
            brand (Optional[str]): Brand filter  
            keywords (Optional[List[str]]): Keywords filter
            top_search_results (int): Number of results
            
        Returns:
            Dict: Search parameters
        """
        context_enhanced = False
        
        # Use context to enhance content_type if not provided
        if not content_type and search_context.preferred_content_types:
            content_type = search_context.preferred_content_types[-1]
            context_enhanced = True
        
        # Use context to enhance brand if not provided
        if not brand and len(search_context.mentioned_brands) >= 2:
            brand_counts = {}
            for brand_name in search_context.mentioned_brands:
                brand_counts[brand_name] = brand_counts.get(brand_name, 0) + 1
            most_mentioned = max(brand_counts.items(), key=lambda x: x[1])
            if most_mentioned[1] >= 2:
                brand = most_mentioned[0].upper()
                context_enhanced = True
        
        # Use context to enhance keywords if not provided
        if not keywords and search_context.recent_topics:
            context_extractor = ContextExtractor()
            recent_topic_names = search_context.recent_topics[-3:]
            keywords = context_extractor.map_topic_names_to_keywords(recent_topic_names)[:5]
            context_enhanced = True
        
        return {
            "query": query,
            "content_type": content_type,
            "brand": brand,
            "keywords": keywords,
            "top_search_results": top_search_results,
            "context_enhanced": context_enhanced
        }
    
    async def _check_domain_and_respond(self, query: str, search_params: Dict) -> Optional[Dict]:
        """
        Check if query is within domain using LLM-based classification.
        LLM responds with either "YES" (in domain) or "NO" (out of domain).
        
        Args:
            query (str): User query
            search_params (Dict): Search parameters
            
        Returns:
            Optional[Dict]: Domain response if query is out of domain, None if in domain
        """
        try:
            # Use LLM to classify domain
            domain_prompt = CHAT_PROMPTS["domain_check_prompt"].format(query=query)
            
            response = self.openai_client.chat.completions.create(
                messages=[{"role": "user", "content": domain_prompt}],
                model=self.deployment_name,
                temperature=DOMAIN_CHECK_CONFIG.get("llm_temperature"),
                max_tokens=DOMAIN_CHECK_CONFIG.get("llm_max_tokens")
            )
            
            classification_result = response.choices[0].message.content.strip().upper()
            
            # If the classification is "NO", it's out of domain
            if classification_result == "NO":
                return {
                    "answer": CHAT_PROMPTS["out_of_domain_response"],
                    "sources": [],
                    "search_results_count": 0,
                    "query": query,
                    "filters_applied": search_params,
                    "graphrag_enhanced": False,
                    "combined_relevance_score": 0.0,
                    "retrieval_metadata": {"domain_check": "out_of_domain"}
                }
            
            # If the classification is "YES", proceed with search
            return None

        # If LLM fails, allow query to proceed    
        except Exception as e:
            logger.error(f"Domain classification failed: {str(e)}")
            return None
    
    def _create_no_results_response(self, query: str, search_params: Dict) -> Dict:
        """
        Create response when no search results are found.
        
        Args:
            query (str): User query
            search_params (Dict): Search parameters
            
        Returns:
            Dict: No results response
        """
        return {
            "answer": CHAT_PROMPTS["no_results_message"],
            "sources": [],
            "search_results_count": 0,
            "query": query,
            "filters_applied": search_params,
            "graphrag_enhanced": False,
            "combined_relevance_score": 0.0,
            "retrieval_metadata": {
                "search_attempted": True,
                "no_results_reason": "No matching content found"
            }
        }
    
    def _create_final_response(self, answer: str, search_results: List[Dict], 
                                       source_links: List[Dict], query: str, 
                                       search_params: Dict, graphrag_result) -> Dict:
        """
        Create the final response structure.
        
        Args:
            answer (str): Generated answer
            search_results (List[Dict]): Search results
            source_links (List[Dict]): Formatted source links
            query (str): Original query
            search_params (Dict): Search parameters
            graphrag_result: GraphRAGResult object or None
            
        Returns:
            Dict: Final response structure
        """
        graphrag_enhanced = graphrag_result is not None
        combined_relevance_score = 0.0
        
        if graphrag_enhanced and hasattr(graphrag_result, 'combined_score'):
            combined_relevance_score = graphrag_result.combined_score
        
        return {
            "answer": answer,
            "sources": source_links,
            "search_results_count": len(search_results),
            "query": query,
            "filters_applied": {
                "content_type": search_params.get("content_type"),
                "brand": search_params.get("brand"),
                "keywords": search_params.get("keywords")
            },
            "graphrag_enhanced": graphrag_enhanced,
            "combined_relevance_score": combined_relevance_score,
            "retrieval_metadata": {
                "search_method": "hybrid_vector_keyword",
                "total_results": len(search_results),
                "enhanced_context": search_params.get("context_enhanced"),
                "graphrag_metadata": graphrag_result.retrieval_metadata if graphrag_result else {}
            }
        } 