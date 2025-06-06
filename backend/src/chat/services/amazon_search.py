import aiohttp
import asyncio
import logging
import re
import html
import random
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
        self.user_agents = AMAZON_SEARCH_CONFIG["user_agents"]
        self.base_headers = AMAZON_SEARCH_CONFIG["headers"].copy()
        self.affiliate_tag = AMAZON_SEARCH_CONFIG["affiliate_tag"]
        self.selectors = AMAZON_SELECTORS
        self.error_config = ERROR_HANDLING
        self.rate_limit_config = RATE_LIMIT_CONFIG
        
        logger.info("AmazonSearchService initialized successfully")

    def _get_random_headers(self) -> Dict[str, str]:
        """
        Get randomized headers for each request to avoid detection.
        
        Returns:
            Dictionary of headers with randomized User-Agent
        """
        headers = self.base_headers.copy()
        headers["User-Agent"] = random.choice(self.user_agents)
        
        # Add some randomization to other headers
        if random.choice([True, False]):
            headers["DNT"] = "1"
        
        # Randomly vary some header values
        accept_lang_options = [
            "en-US,en;q=0.9",
            "en-US,en;q=0.9,fr;q=0.8",
            "en-CA,en;q=0.9,fr;q=0.8"
        ]
        headers["Accept-Language"] = random.choice(accept_lang_options)
        
        return headers

    def _build_search_url(self, query: str, category: Optional[str] = None) -> str:
        """
        Build Amazon search URL with proper encoding and parameters.
        
        Args:
            query: Search query string
            category: Product category for targeted search
            
        Returns:
            Complete Amazon search URL
        """
        enhanced_query = f"{query} nestle"
        encoded_query = quote_plus(enhanced_query.strip())
        
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

    def _is_nestle_product(self, title: str) -> bool:
        """
        Check if product title indicates it's a Nestlé product based on brand patterns.
        
        Args:
            title: Product title to check
            
        Returns:
            True if product appears to be from Nestlé
        """
        if not title:
            return False
            
        title_lower = title.lower()
        
        try:
            from backend.config.brands import get_all_brand_variations
        except ImportError:
            from config.brands import get_all_brand_variations
        
        nestle_brands = [brand.lower() for brand in get_all_brand_variations()]
        
        return any(brand in title_lower for brand in nestle_brands)

    def _calculate_product_score(self, title: str, price: Optional[str], rating: Optional[str]) -> float:
        """
        Calculate a relevance score for the product to prioritize Nestlé products.
        
        Args:
            title: Product title
            price: Product price
            rating: Product rating
            
        Returns:
            Relevance score (higher is better)
        """
        score = 0.0
        
        # Base score for Nestlé products
        if self._is_nestle_product(title):
            score += 10.0  # High bonus for Nestlé products
        
        # Rating bonus
        if rating:
            try:
                if '/' in rating:
                    rating_value = float(rating.split('/')[0])
                else:
                    rating_value = float(rating)
                score += rating_value  # Add rating value to score
            except (ValueError, IndexError):
                pass
        
        # Price availability bonus
        if price and price != 'Price unavailable':
            score += 1.0
        
        return score

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
        
        # Remove common prefixes
        cleaned = re.sub(r'^(CAD|CDN|\$|Price:|From:)\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Extract numeric price with proper formatting
        price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', cleaned)
        if price_match:
            price_value = price_match.group(1)
            return f"${price_value}"
        
        if re.match(r'^\$?\d+[\d,]*\.?\d*$', cleaned):
            return f"${cleaned.lstrip('$')}" if not cleaned.startswith('$') else cleaned
            
        return None

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

    def _clean_title(self, title_text: str) -> Optional[str]:
        """
        Clean and format title text from Amazon.
        
        Args:
            title_text: Raw title text from Amazon
            
        Returns:
            Cleaned title string or None
        """
        if not title_text:
            return None
            
        # Decode HTML entities
        cleaned = html.unescape(title_text.strip())
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove common unwanted patterns and redundant information
        patterns_to_remove = [
            r'\([^)]*Brand\)',
            r'\([^)]*Packaging may vary\)',
            r'\([^)]*Pack of \d+\)',
            r'\([^)]*\d+\s*ct\)',
            r'\([^)]*Count\)',
            r'Visit the .* Store',
            r'by .*$',
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove redundant brand mentions
        words = cleaned.split()
        seen_words = set()
        filtered_words = []
        
        for word in words:
            word_lower = word.lower().strip(',.')
            if word_lower not in seen_words or len(word_lower) <= 3:
                filtered_words.append(word)
                seen_words.add(word_lower)
        
        cleaned = ' '.join(filtered_words)
        
        # Remove size/weight duplicates
        size_patterns = [
            r'(\d+\.?\d*\s*(?:g|oz|lb|kg|ml|l))[^,]*,\s*\1\s*(?:grams?|ounces?|pounds?|kilograms?|milliliters?|liters?)',
            r'(\d+\.?\d*)\s*(?:grams?|ounces?|pounds?).*?,\s*\1\s*(?:g|oz|lb)',
        ]
        
        for pattern in size_patterns:
            cleaned = re.sub(pattern, r'\1', cleaned, flags=re.IGNORECASE)
        
        if len(cleaned) > 50:
            words = cleaned.split()
            
            if len(words) > 8:
                if len(words) > 12:
                    cleaned = ' '.join(words[:3] + ['...'] + words[-2:])
                else:
                    cleaned = ' '.join(words[:6]) + '...'
            elif len(cleaned) > 50:
                cleaned = cleaned[:47] + '...'
        
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        cleaned = re.sub(r',\s*,', ',', cleaned)
        cleaned = re.sub(r',\s*$', '', cleaned)
        
        return cleaned if cleaned and len(cleaned) > 2 else None

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
                # Add random delay before request
                if attempt > 0:
                    delay_range = self.error_config.get("random_delay_range", (2, 8))
                    delay = random.uniform(delay_range[0], delay_range[1])
                    logger.info(f"Adding random delay of {delay:.2f}s before retry {attempt + 1}")
                    await asyncio.sleep(delay)
                
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(search_url, headers=self._get_random_headers()) as response:
                        
                        if response.status == 200:
                            html_content = await response.text()
                            logger.debug(f"Successfully fetched search results (attempt {attempt + 1})")
                            return html_content
                            
                        elif response.status == 429:
                            wait_time = self.error_config["rate_limit_delay"] * (attempt + 1)
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        elif response.status == 503:
                            wait_time = self.error_config["retry_delay"] * (self.error_config["backoff_factor"] ** attempt)
                            logger.warning(f"Service unavailable (503), waiting {wait_time}s before retry {attempt + 1}")
                            await asyncio.sleep(wait_time)
                            continue
                            
                        else:
                            logger.warning(f"HTTP {response.status} on attempt {attempt + 1}: {search_url}")
                            if attempt < self.error_config["max_retries"] - 1:
                                wait_time = self.error_config["retry_delay"] * (self.error_config["backoff_factor"] ** attempt)
                                await asyncio.sleep(wait_time)
                            
            except asyncio.TimeoutError:
                wait_time = self.error_config["retry_delay"] * (self.error_config["backoff_factor"] ** attempt)
                logger.warning(f"Timeout on attempt {attempt + 1}, waiting {wait_time}s")
                if attempt < self.error_config["max_retries"] - 1:
                    await asyncio.sleep(wait_time)
                
            except Exception as e:
                wait_time = self.error_config["retry_delay"] * (self.error_config["backoff_factor"] ** attempt)
                logger.warning(f"Error on attempt {attempt + 1}: {str(e)}, waiting {wait_time}s")
                if attempt < self.error_config["max_retries"] - 1:
                    await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to fetch search results after {self.error_config['max_retries']} attempts")
        return None

    def _parse_products_from_html(self, html_content: str) -> List[AmazonProduct]:
        """
        Parse product information from Amazon search results HTML.
        
        Args:
            html_content: HTML content from Amazon search
            
        Returns:
            List of AmazonProduct objects sorted by relevance (Nestlé products first)
        """
        products_with_scores = []
        
        try:
            # Find product containers
            product_pattern = r'data-component-type="s-search-result"[^>]*>(.*?)(?=data-component-type="s-search-result"|$)'
            product_matches = re.findall(product_pattern, html_content, re.DOTALL)
            parse_limit = min(len(product_matches), self.max_results * 2)
            
            for i, product_html in enumerate(product_matches[:parse_limit]):
                try:
                    # Extract title
                    title = None
                    title_patterns = [
                        r'<span[^>]*data-a-size="[^"]*"[^>]*>([^<]+)</span>.*?<h2',
                        r'<h2[^>]*>.*?<a[^>]*title="([^"]+)"',
                        r'<h2[^>]*>.*?<span[^>]*class="[^"]*a-size-[^"]*"[^>]*>([^<]+)</span>',
                        r'<h2[^>]*>.*?<span[^>]*>([^<]+)</span>',
                        r'aria-label="([^"]+)"[^>]*>[^<]*<h2',
                        r'<h2[^>]*>.*?<a[^>]*>.*?<span[^>]*>([^<]+)</span>',
                        r'data-cy="title-recipe-link"[^>]*>([^<]+)<',
                    ]
                    
                    for pattern_idx, pattern in enumerate(title_patterns):
                        title_match = re.search(pattern, product_html, re.DOTALL)
                        if title_match:
                            raw_title = title_match.group(1).strip()
                            if pattern_idx < 2 and len(raw_title.split()) < 3:
                                continue
                            title = self._clean_title(raw_title)
                            if title and len(title) > 5:
                                logger.debug(f"Product {i}: Found title using pattern {pattern_idx}: '{title[:30]}...'")
                                break
                    
                    if not title:
                        generic_patterns = [
                            r'<h2[^>]*>(.*?)</h2>',
                            r'<a[^>]*title="([^"]+)"', 
                            r'alt="([^"]+)"[^>]*class="[^"]*s-image',
                            r'<span[^>]*class="[^"]*a-size-base-plus[^"]*"[^>]*>([^<]+)</span>',  # Base plus size
                        ]
                        
                        for pattern_idx, pattern in enumerate(generic_patterns):
                            title_match = re.search(pattern, product_html, re.DOTALL)
                            if title_match:
                                raw_title = re.sub(r'<[^>]*>', '', title_match.group(1)).strip()
                                title = self._clean_title(raw_title)
                                if title and len(title) > 5:
                                    logger.debug(f"Product {i}: Found title using generic pattern {pattern_idx}: '{title[:30]}...'")
                                    break
                    
                    if not title or len(title) <= 5:
                        fallback_title = "Amazon Product"
                        
                        img_alt_match = re.search(r'alt="([^"]*(?:nestle|kit\s*kat|nescafe|smarties)[^"]*)"', product_html, re.IGNORECASE)
                        if img_alt_match:
                            fallback_title = self._clean_title(img_alt_match.group(1)) or fallback_title
                        
                        title = fallback_title
                        logger.warning(f"Product {i}: Using fallback title: '{title}'")
                    
                    # Extract URL 
                    product_url = None
                    url_patterns = [
                        r'href="(/[^"]*dp/[^"]*)"',
                        r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"',
                        r'<a[^>]*href="([^"]+)"[^>]*>.*?<h2',
                    ]
                    
                    for pattern in url_patterns:
                        url_match = re.search(pattern, product_html, re.DOTALL)
                        if url_match:
                            relative_url = url_match.group(1)
                            if relative_url and not relative_url.startswith('javascript:'):
                                product_url = urljoin(self.base_url, relative_url)
                                break
                    
                    # Extract price
                    price = None
                    price_patterns = [
                        r'<span[^>]*class="[^"]*a-offscreen[^"]*"[^>]*>\$?([0-9,]+\.?[0-9]*)</span>',
                        r'<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>([^<]+)</span>',
                        r'<span[^>]*class="[^"]*a-price[^"]*"[^>]*>[^<]*<[^>]*>\$?([0-9,]+\.?[0-9]*)<',
                    ]
                    
                    for pattern in price_patterns:
                        price_match = re.search(pattern, product_html)
                        if price_match:
                            price = self._clean_price(price_match.group(1))
                            break
                    
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
                        
                        # Calculate relevance score
                        score = self._calculate_product_score(title, price, rating)
                        
                        product = AmazonProduct(
                            title=title,
                            price=price,
                            rating=rating,
                            image_url=image_url,
                            product_url=affiliate_url,
                            asin=asin,
                            is_sponsored=is_sponsored
                        )
                        
                        products_with_scores.append((score, product))
                        
                except Exception as e:
                    logger.warning(f"Error parsing product {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
        
        # Sort products by score and take the top results
        products_with_scores.sort(key=lambda x: x[0], reverse=True)
        sorted_products = [product for score, product in products_with_scores[:self.max_results]]
        
        logger.info(f"Successfully parsed {len(sorted_products)} products from search results")
        return sorted_products

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