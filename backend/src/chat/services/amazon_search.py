import aiohttp
import asyncio
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus, urljoin

try:
    from backend.config.amazon_search import (
        AMAZON_SEARCH_CONFIG,
        AMAZON_URL_PATTERNS,
        AMAZON_SELECTORS,
        CATEGORY_SEARCH_PARAMS,
        CATEGORY_DETECTION_KEYWORDS,
        ERROR_HANDLING,
        VALID_PRODUCT_INDICATORS,
        EXCLUDE_PRODUCT_KEYWORDS,
        RATE_LIMIT_CONFIG,
        get_amazon_category_for_brand
    )
except ImportError:
    from config.amazon_search import (
        AMAZON_SEARCH_CONFIG,
        AMAZON_URL_PATTERNS,
        AMAZON_SELECTORS,
        CATEGORY_SEARCH_PARAMS,
        CATEGORY_DETECTION_KEYWORDS,
        ERROR_HANDLING,
        VALID_PRODUCT_INDICATORS,
        EXCLUDE_PRODUCT_KEYWORDS,
        RATE_LIMIT_CONFIG,
        get_amazon_category_for_brand
    )

logger = logging.getLogger(__name__)

@dataclass
class AmazonProduct:
    """Data class for Amazon product information."""
    title: str
    price: Optional[str]
    rating: Optional[str]
    image_url: Optional[str]
    product_url: str
    asin: Optional[str] = None
    is_sponsored: bool = False

class AmazonSearchService:
    """Service for finding products on Amazon using web scraping."""
    
    def __init__(self):
        """Initialize the Amazon Search Service."""
        self.base_url = AMAZON_SEARCH_CONFIG["base_url"]
        self.search_endpoint = AMAZON_SEARCH_CONFIG["search_endpoint"]
        self.timeout = AMAZON_SEARCH_CONFIG["timeout"]
        self.max_results = AMAZON_SEARCH_CONFIG["max_results"]
        self.user_agent = AMAZON_SEARCH_CONFIG["user_agent"]
        self.headers = AMAZON_SEARCH_CONFIG["headers"].copy()
        self.headers["User-Agent"] = self.user_agent
        self.affiliate_tag = AMAZON_SEARCH_CONFIG["affiliate_tag"]
        self.selectors = AMAZON_SELECTORS
        self.error_config = ERROR_HANDLING
        self.rate_limit_config = RATE_LIMIT_CONFIG
        
        logger.info("AmazonSearchService initialized successfully")

    def _build_search_url(self, query: str, category: Optional[str] = None) -> str:
        """
        Build Amazon search URL with proper encoding and parameters.
        
        Args:
            query: Search query string
            category: Product category for targeted search
            
        Returns:
            Complete Amazon search URL
        """
        encoded_query = quote_plus(query.strip())
        
        # Enhanced category detection using brand information
        if not category:
            category = self._detect_category_from_query(query)
        
        # Get category-specific parameters
        category_params = CATEGORY_SEARCH_PARAMS.get(
            category or "default", 
            CATEGORY_SEARCH_PARAMS["default"]
        )
        
        # Build base URL with search parameters
        search_url = f"{self.base_url}{self.search_endpoint}?k={encoded_query}"
        
        # Add category-specific parameters
        for param, value in category_params.items():
            search_url += f"&{param}={value}"
        
        logger.debug(f"Built search URL: {search_url} (category: {category})")
        return search_url

    def _detect_category_from_query(self, query: str) -> str:
        """
        Detect the appropriate Amazon category based on the search query.
        
        Args:
            query: Search query string
            
        Returns:
            Category name for Amazon search
        """
        try:
            from backend.config.brands import normalize_brand_name
        except ImportError:
            from config.brands import normalize_brand_name
        
        query_lower = query.lower()
        
        # Check for category keywords
        for category, keywords in CATEGORY_DETECTION_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                logger.debug(f"Detected category '{category}' from keywords")
                return category
        
        # Fallback to find brand names in the query
        for brand_indicator in VALID_PRODUCT_INDICATORS:
            if brand_indicator in query_lower:
                normalized_brand = normalize_brand_name(brand_indicator)
                if normalized_brand:
                    category = get_amazon_category_for_brand(normalized_brand)
                    if category != "default":
                        logger.debug(f"Detected brand '{normalized_brand}' -> category '{category}'")
                        return category
        
        return "default"

    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """
        Extract ASIN (Amazon Standard Identification Number) from product URL.
        
        Args:
            url: Amazon product URL
            
        Returns:
            ASIN string if found, None otherwise
        """
        if not url:
            return None
            
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
            r'/([A-Z0-9]{10})/'
        ]
        
        for pattern in asin_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def _generate_affiliate_url(self, product_url: str, asin: Optional[str] = None) -> str:
        """
        Generate affiliate URL if affiliate tag is configured.
        
        Args:
            product_url: Original Amazon product URL
            asin: Product ASIN (optional)
            
        Returns:
            Affiliate URL or original URL if no affiliate tag
        """
        if not self.affiliate_tag:
            return product_url
            
        # Extract ASIN if not provided
        if not asin:
            asin = self._extract_asin_from_url(product_url)
        
        if asin:
            return AMAZON_URL_PATTERNS["affiliate_url"].format(
                asin=asin, 
                affiliate_tag=self.affiliate_tag
            )
        
        # Fallback to append affiliate tag to existing URL
        separator = "&" if "?" in product_url else "?"
        return f"{product_url}{separator}tag={self.affiliate_tag}"

    def _is_valid_product(self, title: str, url: str) -> bool:
        """
        Validate if the product is relevant and of good quality.
        
        Args:
            title: Product title
            url: Product URL
            
        Returns:
            True if product meets quality standards
        """
        if not title or not url:
            return False
            
        title_lower = title.lower()
        
        for keyword in EXCLUDE_PRODUCT_KEYWORDS:
            if keyword in title_lower:
                logger.debug(f"Product excluded due to keyword '{keyword}': {title[:50]}")
                return False
        
        if not any(pattern in url for pattern in ["/dp/", "/gp/product/", "amazon.ca"]):
            return False
            
        return True

    def _clean_price(self, price_text: str) -> Optional[str]:
        """
        Clean and format price text from Amazon.
        
        Args:
            price_text: Raw price text from Amazon
            
        Returns:
            Cleaned price string or None
        """
        if not price_text:
            return None
            
        cleaned = re.sub(r'\s+', ' ', price_text.strip())
        cleaned = re.sub(r'^(CAD|CDN|\$|Price:|From:)\s*', '', cleaned, flags=re.IGNORECASE)
        
        price_match = re.search(r'[\$]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', cleaned)
        if price_match:
            return f"${price_match.group(1)}"
            
        return cleaned if cleaned else None

    def _clean_rating(self, rating_text: str) -> Optional[str]:
        """
        Clean and format rating text from Amazon.
        
        Args:
            rating_text: Raw rating text from Amazon
            
        Returns:
            Cleaned rating string or None
        """
        if not rating_text:
            return None
            
        rating_match = re.search(r'(\d+\.?\d*)\s*out\s*of\s*5', rating_text, re.IGNORECASE)
        if rating_match:
            return f"{rating_match.group(1)}/5"
            
        simple_rating = re.search(r'(\d+\.?\d*)', rating_text)
        if simple_rating:
            rating_val = float(simple_rating.group(1))
            if 0 <= rating_val <= 5:
                return f"{rating_val}/5"
                
        return None

    async def _fetch_search_results(self, search_url: str) -> Optional[str]:
        """
        Fetch search results HTML from Amazon with proper error handling.
        
        Args:
            search_url: Complete Amazon search URL
            
        Returns:
            HTML content or None on error
        """
        for attempt in range(self.error_config["max_retries"]):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        
                        if response.status == 200:
                            html_content = await response.text()
                            logger.debug(f"Successfully fetched search results (attempt {attempt + 1})")
                            return html_content
                            
                        elif response.status == 429:
                            wait_time = self.error_config["rate_limit_delay"] * (attempt + 1)
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        else:
                            logger.warning(f"HTTP {response.status} on attempt {attempt + 1}: {search_url}")
                            
            except asyncio.TimeoutError:
                wait_time = self.error_config["retry_delay"] * (self.error_config["backoff_factor"] ** attempt)
                logger.warning(f"Timeout on attempt {attempt + 1}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                wait_time = self.error_config["retry_delay"] * (self.error_config["backoff_factor"] ** attempt)
                logger.warning(f"Error on attempt {attempt + 1}: {str(e)}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to fetch search results after {self.error_config['max_retries']} attempts")
        return None

    def _parse_products_from_html(self, html_content: str) -> List[AmazonProduct]:
        """
        Parse product information from Amazon search results HTML.
        
        Args:
            html_content: HTML content from Amazon search
            
        Returns:
            List of AmazonProduct objects
        """
        products = []
        
        try:
            # Find product containers
            product_pattern = r'data-component-type="s-search-result"[^>]*>(.*?)(?=data-component-type="s-search-result"|$)'
            product_matches = re.findall(product_pattern, html_content, re.DOTALL)
            
            for i, product_html in enumerate(product_matches[:self.max_results]):
                try:
                    # Extract title
                    title_match = re.search(r'<h2[^>]*>.*?<span[^>]*>([^<]+)</span>', product_html, re.DOTALL)
                    title = title_match.group(1).strip() if title_match else None
                    
                    # Extract URL
                    url_match = re.search(r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"', product_html, re.DOTALL)
                    relative_url = url_match.group(1) if url_match else None
                    product_url = urljoin(self.base_url, relative_url) if relative_url else None
                    
                    # Extract price
                    price_match = re.search(r'<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>([^<]+)</span>', product_html)
                    price = self._clean_price(price_match.group(1)) if price_match else None
                    
                    # Extract rating
                    rating_match = re.search(r'<span[^>]*class="[^"]*a-icon-alt[^"]*"[^>]*>([^<]+)</span>', product_html)
                    rating = self._clean_rating(rating_match.group(1)) if rating_match else None
                    
                    # Extract image URL
                    img_match = re.search(r'<img[^>]*class="[^"]*s-image[^"]*"[^>]*src="([^"]+)"', product_html)
                    image_url = img_match.group(1) if img_match else None
                    
                    # Check if sponsored
                    is_sponsored = 'puis-sponsored-label-text' in product_html
                    
                    # Validate product
                    if title and product_url and self._is_valid_product(title, product_url):
                        asin = self._extract_asin_from_url(product_url)
                        affiliate_url = self._generate_affiliate_url(product_url, asin)
                        
                        product = AmazonProduct(
                            title=title,
                            price=price,
                            rating=rating,
                            image_url=image_url,
                            product_url=affiliate_url,
                            asin=asin,
                            is_sponsored=is_sponsored
                        )
                        
                        products.append(product)
                        logger.debug(f"Parsed product: {title[:50]}...")
                    
                except Exception as e:
                    logger.warning(f"Error parsing product {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
            
        logger.info(f"Successfully parsed {len(products)} products from search results")
        return products

    async def search_products(self, query: str, category: Optional[str] = None) -> List[AmazonProduct]:
        """
        Search for products on Amazon.
        
        Args:
            query: Search query string
            category: Optional product category for targeted search
            
        Returns:
            List of AmazonProduct objects
        """
        if not query or not query.strip():
            logger.warning("Empty search query provided")
            return []
            
        logger.info(f"Searching Amazon for: {query} (category: {category or 'default'})")
        
        try:
            # Build search URL
            search_url = self._build_search_url(query, category)
            
            # Fetch search results
            html_content = await self._fetch_search_results(search_url)
            if not html_content:
                return []
            
            # Parse products from HTML
            products = self._parse_products_from_html(html_content)
            
            logger.info(f"Found {len(products)} valid products for query: {query}")
            return products
            
        except Exception as e:
            logger.error(f"Error searching Amazon for '{query}': {str(e)}")
            return []

    def format_products_for_response(self, products: List[AmazonProduct]) -> List[Dict]:
        """
        Format Amazon products for frontend display.
        
        Args:
            products: List of AmazonProduct objects
            
        Returns:
            List of formatted product dictionaries
        """
        formatted_products = []
        
        for i, product in enumerate(products):
            formatted_product = {
                "id": i + 1,
                "title": product.title,
                "price": product.price,
                "rating": product.rating,
                "image_url": product.image_url,
                "product_url": product.product_url,
                "asin": product.asin,
                "is_sponsored": product.is_sponsored,
                "platform": "Amazon"
            }
            formatted_products.append(formatted_product)
            
        return formatted_products 