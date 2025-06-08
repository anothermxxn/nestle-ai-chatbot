import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from openai import AzureOpenAI

if TYPE_CHECKING:
    from .session_service import ConversationMessage
    from .context_service import SearchContext, ContextExtractor

try:
    from backend.src.search.services.azure_search import AzureSearchClient
    from backend.src.search.services.graphrag import GraphRAGClient
    from backend.src.chat.formatters.graphrag_formatter import GraphRAGFormatter
    from backend.src.chat.services.context_service import SearchContext, ContextExtractor
    from backend.config import (
        AZURE_OPENAI_CONFIG,
        CHAT_CONFIG,
        DOMAIN_CHECK_CONFIG,
        SYSTEM_PROMPT,
        DOMAIN_CHECK_PROMPT,
        OUT_OF_DOMAIN_PROMPT,
        NO_RESULTS_MESSAGE,
        ERROR_MESSAGE,
        GENERATION_ERROR_MESSAGE,
        PURCHASE_CHECK_PROMPT,
        PURCHASE_ASSISTANCE_PROMPT,
        COUNT_CHECK_PROMPT,
        COUNT_RESPONSE_PROMPT,
        PURCHASE_FALLBACK_BASE,
        PURCHASE_FALLBACK_BOTH_AVAILABLE,
        PURCHASE_FALLBACK_STORES_ONLY,
        PURCHASE_FALLBACK_AMAZON_ONLY,
        PURCHASE_FALLBACK_LOCATION_NEEDED,
        PURCHASE_FALLBACK_NEITHER_AVAILABLE,
        PURCHASE_FALLBACK_AMAZON_BLOCKED,
    )
    from backend.src.chat.services.amazon_search import AmazonSearchService
    from backend.src.chat.services.store_locator import StoreLocatorService
    from backend.src.graph.services.count_service import CountStatisticsService
except ImportError:
    from src.search.services.azure_search import AzureSearchClient
    from src.search.services.graphrag import GraphRAGClient
    from src.chat.formatters.graphrag_formatter import GraphRAGFormatter
    from src.chat.services.context_service import SearchContext, ContextExtractor
    from config import (
        AZURE_OPENAI_CONFIG,
        CHAT_CONFIG,
        DOMAIN_CHECK_CONFIG,
        SYSTEM_PROMPT,
        DOMAIN_CHECK_PROMPT,
        OUT_OF_DOMAIN_PROMPT,
        NO_RESULTS_MESSAGE,
        ERROR_MESSAGE,
        GENERATION_ERROR_MESSAGE,
        PURCHASE_CHECK_PROMPT,
        PURCHASE_ASSISTANCE_PROMPT,
        COUNT_CHECK_PROMPT,
        COUNT_RESPONSE_PROMPT,
        PURCHASE_FALLBACK_BASE,
        PURCHASE_FALLBACK_BOTH_AVAILABLE,
        PURCHASE_FALLBACK_STORES_ONLY,
        PURCHASE_FALLBACK_AMAZON_ONLY,
        PURCHASE_FALLBACK_LOCATION_NEEDED,
        PURCHASE_FALLBACK_NEITHER_AVAILABLE,
        PURCHASE_FALLBACK_AMAZON_BLOCKED,
    )
    from src.chat.services.amazon_search import AmazonSearchService
    from src.chat.services.store_locator import StoreLocatorService
    from src.graph.services.count_service import CountStatisticsService
    

logger = logging.getLogger(__name__)

class NestleChatClient:
    """
    Chat client that combines Azure AI Search, Azure Cosmos DB with Azure OpenAI for 
    conversational search over Nestle content. 
    Enhanced with integrated purchase assistance features.
    """
    
    def __init__(self):
        """Initialize chat client with all required services."""
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
        
        # Initialize services for purchase assistance
        self.amazon_search = AmazonSearchService()
        self.store_locator = StoreLocatorService()
        
        # Initialize count statistics service
        self.count_service = CountStatisticsService()
        
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
    
    async def _perform_hybrid_search(self, search_params: Dict, top_search_results: int):
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

    async def _perform_basic_search(self, search_params: Dict, top_search_results: int):
        """
        Perform basic vector-only search for purchase queries to avoid expensive GraphRAG processing.
        
        Args:
            search_params (Dict): Search parameters including query and filters
            top_search_results (int): Number of results
            
        Returns:
            Tuple[List[Dict], None]: Search results and None (no graph context)
        """
        try:
            logger.info("Using basic vector search for purchase query")
            search_results = await self.search_client.search(
                query=search_params.get("query"),
                top=top_search_results,
                content_type=search_params.get("content_type"),
                brand=search_params.get("brand"),
                keywords=search_params.get("keywords")
            )
            logger.info(f"Basic search returned {len(search_results)} results")
            return search_results, None
            
        except Exception as e:
            logger.error(f"Basic search failed: {str(e)}")
            return [], None

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
        prompt_template = SYSTEM_PROMPT
        
        # Format conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nCONVERSATION HISTORY:\n"
            for msg in conversation_history:
                role = "User" if msg.role == "user" else "Assistant"
                conversation_context += f"{role}: {msg.content}\n"
            conversation_context += f"\nCURRENT QUESTION: {query}\n"
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
        return answer if answer else GENERATION_ERROR_MESSAGE

    async def _check_purchase_intent(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Check if the user query expresses purchase intent using LLM classification
        and extract the specific product name.
        
        Args:
            query (str): User query to analyze
            
        Returns:
            tuple[bool, Optional[str]]: (purchase_intent_detected, extracted_product_name)
        """
        try:
            prompt = PURCHASE_CHECK_PROMPT.format(query=query)
            
            logger.info(f"Checking purchase intent for query: '{query}'")
            logger.debug(f"Purchase check prompt: {prompt}")
            
            response = self.openai_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.deployment_name,
                temperature=0.1,
                max_tokens=50  # Increased to accommodate product name extraction
            )
            
            if response.choices and len(response.choices) > 0:
                result = response.choices[0].message.content.strip()
                logger.info(f"Purchase intent detection result for '{query}': '{result}'")
                
                # Parse the structured response
                intent_detected = False
                extracted_product = None
                
                for line in result.split('\n'):
                    line = line.strip()
                    if line.startswith('INTENT:'):
                        intent_value = line.replace('INTENT:', '').strip().upper()
                        intent_detected = intent_value == "YES"
                    elif line.startswith('PRODUCT:'):
                        product_value = line.replace('PRODUCT:', '').strip()
                        if product_value.upper() != "NONE":
                            extracted_product = product_value
                
                logger.info(f"Purchase intent detected: {intent_detected}")
                if extracted_product:
                    logger.info(f"Extracted product name: '{extracted_product}'")
                
                return intent_detected, extracted_product
            else:
                logger.warning(f"No response choices for purchase intent detection")
                return False, None
            
        except Exception as e:
            logger.error(f"Error in purchase intent detection: {str(e)}")
            
        return False, None

    async def _get_purchase_assistance_data(self, query: str, user_location: Optional[Dict] = None, extracted_product: Optional[str] = None) -> Dict:
        """
        Get purchase assistance data (stores and Amazon products) with status tracking.
        
        Args:
            query: Search query
            user_location: User location for store search
            extracted_product: Extracted product name for targeted search
            
        Returns:
            Dictionary with stores, amazon_products, and status information
        """
        stores = []
        amazon_products = []
        
        # Track status of each service
        nearby_stores_available = False
        amazon_link_available = False
        amazon_blocked = False
        
        # Use extracted product if available, otherwise use query
        search_term = extracted_product if extracted_product else query
        
        # Get store locations
        if user_location and user_location.get('lat') and user_location.get('lon'):
            try:
                store_results = await self.store_locator.find_nearby_stores(
                    lat=user_location['lat'],
                    lon=user_location['lon']
                )
                stores = self.store_locator.format_stores_for_response(store_results[:3])
                nearby_stores_available = len(stores) > 0
                logger.info(f"Found {len(stores)} nearby stores for location")
            except Exception as e:
                logger.warning(f"Store locator failed: {str(e)}")
                stores = []
                nearby_stores_available = False
        else:
            logger.info("No user location provided for nearby store suggestions")
            nearby_stores_available = False
        
        # Get Amazon products
        try:
            amazon_results = await self.amazon_search.search_products(search_term)
            amazon_products = self.amazon_search.format_products_for_response(amazon_results[:3])
            amazon_link_available = len(amazon_products) > 0
            logger.info(f"Amazon search for '{search_term}' returned {len(amazon_products)} products")
        except Exception as e:
            error_msg = str(e).lower()
            logger.warning(f"Amazon search failed: {str(e)}")
            
            if "503" in error_msg:
                # Amazon is blocking (503 error)
                amazon_blocked = True
                amazon_link_available = False
                logger.warning("Amazon appears to be blocking bot requests (503 error)")
            else:
                amazon_blocked = False
                fallback_query = f"{query} nestle"
                fallback_url = self.amazon_search._build_search_url(search_term)
                amazon_products = [{
                    "id": 1,
                    "title": f"Search for '{fallback_query}' on Amazon",
                    "price": "Click to see prices",
                    "rating": None,
                    "image_url": None,
                    "product_url": fallback_url,
                    "asin": None,
                    "is_sponsored": False,
                    "platform": "Amazon"
                }]
                amazon_link_available = True
                logger.info(f"Generated fallback Amazon search link for '{search_term}'")
        
        return {
            "stores": stores,
            "amazon_products": amazon_products,
            "purchase_info": {
                "nearby_stores_available": nearby_stores_available,
                "amazon_link_available": amazon_link_available,
                "amazon_blocked": amazon_blocked
            }
        }

    async def _handle_purchase_query(self, query: str, search_results: List[Dict], user_location: Optional[Dict] = None, extracted_product: Optional[str] = None) -> Dict:
        """
        Handle purchase queries.
        
        Args:
            query: Original user query
            search_results: Search results for product identification
            user_location: User's location for store search
            extracted_product: Extracted product name for targeted search
            
        Returns:
            Dictionary with purchase assistance response
        """
        try:
            # Get purchase assistance data
            purchase_data = await self._get_purchase_assistance_data(query, user_location, extracted_product)
            
            # Extract purchase info for the prompt
            purchase_info = purchase_data.get("purchase_info", {})
            
            # Format sources for the prompt
            sources_text = ""
            if search_results:
                sources_text = "\n".join([
                    f"- {result.get('title', 'Untitled')}: {result.get('content', 'No content available')[:200]}..."
                    for result in search_results[:3]
                ])
            else:
                sources_text = "No specific product information found in our knowledge base."
            
            # Create prompt
            purchase_prompt = PURCHASE_ASSISTANCE_PROMPT.format(
                query=query,
                sources=sources_text,
                purchase_info=purchase_info
            )
            
            # Generate LLM response
            try:
                response = self.openai_client.chat.completions.create(
                    messages=[{"role": "user", "content": purchase_prompt}],
                    model=self.deployment_name,
                    temperature=CHAT_CONFIG.get("llm_temperature", 0.7),
                    max_tokens=CHAT_CONFIG.get("llm_max_tokens", 1000)
                )
                answer = response.choices[0].message.content.strip()
            except Exception as llm_error:
                logger.error(f"LLM failed for purchase query, using fallback: {str(llm_error)}")
                product_name = extracted_product or "Nestlé products"
                
                # Create tailored fallback message based on available purchase options
                answer = PURCHASE_FALLBACK_BASE.format(product_name=product_name)
                if purchase_info.get("nearby_stores_available") and purchase_info.get("amazon_link_available"):
                    answer += PURCHASE_FALLBACK_BOTH_AVAILABLE
                elif purchase_info.get("nearby_stores_available"):
                    answer += PURCHASE_FALLBACK_STORES_ONLY
                    if purchase_info.get("amazon_blocked"):
                        answer += PURCHASE_FALLBACK_AMAZON_BLOCKED
                elif purchase_info.get("amazon_link_available"):
                    answer += PURCHASE_FALLBACK_AMAZON_ONLY
                    if not purchase_info.get("nearby_stores_available"):
                        answer += PURCHASE_FALLBACK_LOCATION_NEEDED
                else:
                    # Neither service worked
                    answer += PURCHASE_FALLBACK_NEITHER_AVAILABLE
                    if purchase_info.get("amazon_blocked"):
                        answer += PURCHASE_FALLBACK_AMAZON_BLOCKED
                    if not purchase_info.get("nearby_stores_available"):
                        answer += PURCHASE_FALLBACK_LOCATION_NEEDED
            
            # Format source links from search results
            source_links = self._format_links(search_results) if search_results else []
            
            # Prepare purchase assistance data for response (excluding internal purchase_info)
            purchase_assistance_data = {
                "stores": purchase_data.get("stores", []),
                "amazon_products": purchase_data.get("amazon_products", [])
            }
            
            return {
                "answer": answer,
                "sources": source_links,
                "search_results_count": len(search_results),
                "query": query,
                "filters_applied": {},
                "graphrag_enhanced": False,
                "combined_relevance_score": 0.0,
                "retrieval_metadata": {"response_type": "purchase_assistance", "purchase_info": purchase_info},
                "is_purchase_query": True,
                "purchase_assistance": purchase_assistance_data
            }
            
        except Exception as e:
            logger.error(f"Critical error in purchase query handling: {str(e)}")
            return {
                "answer": "I'd be happy to help you find Nestlé products! Let me get some information for you.",
                "sources": [],
                "search_results_count": 0,
                "query": query,
                "filters_applied": {},
                "graphrag_enhanced": False,
                "combined_relevance_score": 0.0,
                "retrieval_metadata": {"response_type": "purchase_assistance", "error": str(e)},
                "is_purchase_query": True,
                "purchase_assistance": {"stores": [], "amazon_products": []}
            }
    
    async def _check_count_intent(self, query: str) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Check if the user query is asking for counts, numbers, statistics, or quantities
        and extract the specific type, category, and brand.
        
        Args:
            query (str): User query to analyze
            
        Returns:
            tuple[bool, Optional[str], Optional[str], Optional[str]]: 
                (count_intent_detected, count_type, category_name, brand_name)
        """
        try:
            prompt = COUNT_CHECK_PROMPT.format(query=query)
            
            logger.info(f"Checking count intent for query: '{query}'")
            logger.debug(f"Count check prompt: {prompt}")
            
            response = self.openai_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.deployment_name,
                temperature=0.1,
                max_tokens=100
            )
            
            if response.choices and len(response.choices) > 0:
                result = response.choices[0].message.content.strip()
                logger.info(f"Count intent detection result for '{query}': '{result}'")
                
                # Parse the structured response
                intent_detected = False
                count_type = None
                category_name = None
                brand_name = None
                
                for line in result.split('\n'):
                    line = line.strip()
                    if line.startswith('INTENT:'):
                        intent_value = line.replace('INTENT:', '').strip().upper()
                        intent_detected = intent_value == "YES"
                    elif line.startswith('TYPE:'):
                        type_value = line.replace('TYPE:', '').strip()
                        if type_value.upper() != "NONE":
                            count_type = type_value
                    elif line.startswith('CATEGORY:'):
                        category_value = line.replace('CATEGORY:', '').strip()
                        if category_value.upper() != "NONE":
                            category_name = category_value
                    elif line.startswith('BRAND:'):
                        brand_value = line.replace('BRAND:', '').strip()
                        if brand_value.upper() != "NONE":
                            brand_name = brand_value
                
                logger.info(f"Count intent detected: {intent_detected}")
                if count_type:
                    logger.info(f"Count type: '{count_type}'")
                if category_name:
                    logger.info(f"Category: '{category_name}'")
                if brand_name:
                    logger.info(f"Brand: '{brand_name}'")
                
                return intent_detected, count_type, category_name, brand_name
            else:
                logger.warning(f"No response choices for count intent detection")
                return False, None, None, None
            
        except Exception as e:
            logger.error(f"Error in count intent detection: {str(e)}")
            
        return False, None, None, None

    async def _handle_count_query(self, query: str, count_type: Optional[str], 
                                  category_filter: Optional[str], brand_filter: Optional[str]) -> Dict:
        """
        Handle count queries by retrieving statistics and formatting natural language response.
        
        Args:
            query (str): Original user query
            count_type (Optional[str]): Type of count requested
            category_filter (Optional[str]): Category filter if applicable
            brand_filter (Optional[str]): Brand filter if applicable
            
        Returns:
            Dict: Count response with natural language explanation
        """
        try:
            logger.info(f"Handling count query: {query}, type: {count_type}, category: {category_filter}, brand: {brand_filter}")
            
            # Gather count statistics based on query type
            count_data = {}
            
            if count_type in ["TOTAL_PRODUCTS", "PRODUCTS_BY_CATEGORY", "PRODUCTS_BY_BRAND"]:
                if brand_filter:
                    # Brand-specific product count
                    brand_counts = await self.count_service.get_product_counts_by_brand()
                    count_data = {"brand_counts": brand_counts, "requested_brand": brand_filter}
                elif category_filter:
                    # Category-specific product count
                    category_counts = await self.count_service.get_product_counts_by_category()
                    count_data = {"category_counts": category_counts, "requested_category": category_filter}
                else:
                    # Total product count
                    entity_counts = await self.count_service.get_entity_counts()
                    count_data = {"total_products": entity_counts.get("product", 0)}
            
            elif count_type == "BRANDS":
                # Brand count
                entity_counts = await self.count_service.get_entity_counts()
                count_data = {"total_brands": entity_counts.get("brand", 0)}
            
            elif count_type == "RECIPES":
                # Recipe count
                recipe_counts = await self.count_service.get_recipe_counts()
                count_data = {"recipe_stats": recipe_counts}
            
            else:
                # General entity counts (fallback)
                entity_counts = await self.count_service.get_entity_counts()
                count_data = {"entity_counts": entity_counts}
            
            # Create prompt for natural language count response
            count_response_prompt = COUNT_RESPONSE_PROMPT.format(
                query=query,
                statistics=str(count_data)
            )
            
            # Generate natural language response
            response = self.openai_client.chat.completions.create(
                messages=[{"role": "user", "content": count_response_prompt}],
                model=self.deployment_name,
                temperature=CHAT_CONFIG.get("llm_temperature", 0.7),
                max_tokens=CHAT_CONFIG.get("llm_max_tokens", 500)
            )
            
            generated_answer = response.choices[0].message.content.strip()
            
            return {
                "answer": generated_answer,
                "sources": [],
                "search_results_count": 0,
                "query": query,
                "filters_applied": {
                    "content_type": None,
                    "brand": brand_filter,
                    "category": category_filter
                },
                "graphrag_enhanced": False,
                "combined_relevance_score": 1.0,
                "retrieval_metadata": {"query_type": "count", "count_data": count_data},
                "is_count_query": True,
                "is_purchase_query": False,
                "count_data": count_data
            }
            
        except Exception as e:
            logger.error(f"Error handling count query: {str(e)}")
            return {
                "answer": "I'm sorry, I couldn't retrieve the count information at the moment. Please try again later.",
                "sources": [],
                "search_results_count": 0,
                "query": query,
                "filters_applied": {},
                "graphrag_enhanced": False,
                "combined_relevance_score": 0.0,
                "retrieval_metadata": {"error": str(e), "query_type": "count"},
                "is_count_query": True,
                "is_purchase_query": False,
                "count_data": {}
            }

    async def search_and_chat(
        self,
        query: str,
        conversation_history: Optional[List['ConversationMessage']] = None,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_search_results: int = 5,
        user_location: Optional[Dict] = None
    ) -> Dict:
        """
        Perform context-aware search and generate a conversational response.
        Enhanced with purchase assistance features and count query handling.
        
        Args:
            query (str): User's question or search query
            conversation_history (Optional[List['ConversationMessage']]): Previous conversation messages as ConversationMessage objects
            content_type (Optional[str]): Filter by content type (e.g., "recipe")
            brand (Optional[str]): Filter by brand (e.g., "Nestle")
            keywords (Optional[List[str]]): Filter by keywords
            top_search_results (int): Number of search results to use as context
            user_location (Optional[Dict]): User's location for store locator {lat, lon}
            
        Returns:
            Dict: Response containing answer, sources, metadata, and purchase assistance data
        """
        try:
            logger.info(f"Processing chat query: {query}")
            
            # Extract search context from conversation history
            search_context = self._extract_search_context_from_history(conversation_history)
            
            # Prepare search parameters
            search_params = self._prepare_search_params(
                query, search_context, content_type, brand, keywords, top_search_results
            )
            
            # Domain check
            domain_response = await self._check_domain_and_respond(query, search_params)
            if domain_response:
                return domain_response
            
            # Count query check
            is_count_query, count_type, category_filter, brand_filter = await self._check_count_intent(query)
            
            if is_count_query:
                logger.info(f"Handling count query: '{query}'")
                return await self._handle_count_query(query, count_type, category_filter, brand_filter)
            
            # Purchase intent check
            is_purchase_query, extracted_product = await self._check_purchase_intent(query)
            
            if is_purchase_query:
                logger.info(f"Handling purchase query: '{query}'" + (f" (product: {extracted_product})" if extracted_product else ""))
                
                # Update search params to use the extracted product name
                if extracted_product:
                    search_params["query"] = extracted_product
                
                # Get basic search results for product identification
                search_results, _ = await self._perform_basic_search(search_params, min(3, top_search_results))
                
                return await self._handle_purchase_query(query, search_results, user_location, extracted_product)
            
            else:
                logger.info(f"Handling regular query: '{query}'")
                # Handle regular query
                formatted_conversation_history = self._format_conversation_history(conversation_history)
                
                search_results, graphrag_result = await self._perform_hybrid_search(
                    search_params, top_search_results
                )
                
                if not search_results:
                    return self._create_no_results_response(query, search_params)
                
                # Generate response
                prompt = self._create_prompt(query, search_results, graphrag_result, formatted_conversation_history)
                source_links = self._format_links(search_results)
                answer = await self._generate_llm_response(prompt)
                
                response = self._create_final_response(
                    answer, search_results, source_links, query, search_params, graphrag_result
                )
                response['is_purchase_query'] = False
                response['is_count_query'] = False
                
                return response
            
        except Exception as e:
            logger.error(f"Error in context-aware search_and_chat: {str(e)}")
            
            return {
                "answer": ERROR_MESSAGE,
                "sources": [],
                "search_results_count": 0,
                "query": query,
                "session_id": None,
                "filters_applied": {
                    "content_type": content_type,
                    "brand": brand,
                    "keywords": keywords
                },
                "graphrag_enhanced": False,
                "combined_relevance_score": 0.0,
                "retrieval_metadata": {"error": str(e), "error_type": "general_failure"},
                "is_purchase_query": False,
                "is_count_query": False,
                "purchase_assistance": None
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
            domain_prompt = DOMAIN_CHECK_PROMPT.format(query=query)
            
            response = self.openai_client.chat.completions.create(
                messages=[{"role": "user", "content": domain_prompt}],
                model=self.deployment_name,
                temperature=DOMAIN_CHECK_CONFIG.get("llm_temperature"),
                max_tokens=DOMAIN_CHECK_CONFIG.get("llm_max_tokens")
            )
            
            classification_result = response.choices[0].message.content.strip().upper()
            
            # If the classification is "NO", it's out of domain
            if classification_result == "NO":
                out_of_domain_prompt = OUT_OF_DOMAIN_PROMPT.format(query=query)
                
                out_of_domain_response = self.openai_client.chat.completions.create(
                    messages=[{"role": "user", "content": out_of_domain_prompt}],
                    model=self.deployment_name,
                    temperature=CHAT_CONFIG.get("llm_temperature"),
                    max_tokens=CHAT_CONFIG.get("llm_max_tokens")
                )
                
                generated_answer = out_of_domain_response.choices[0].message.content.strip()
                
                return {
                    "answer": generated_answer,
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
            "answer": NO_RESULTS_MESSAGE,
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