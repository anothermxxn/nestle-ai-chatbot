"""URL parsing utilities for the Nestle AI Chatbot."""

import re
from typing import Dict, List, Optional
from urllib.parse import unquote, urlparse
import logging
from html import unescape

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Known content types and their URL patterns
CONTENT_TYPES = {
    "recipe": ["recipe", "recipes", "cooking", "meal-ideas", "meal-planning"],
    "news": ["news", "media", "press-release", "press-releases", "media-library", "announcements"],
    "about": ["about", "about-us", "company", "our-company", "history", "heritage"],
    "brand": ["brands", "our-brands"],
    "product": ["products", "product-details", "ranges"],
    "nutrition": ["nutrition", "health", "wellness", "nutrition-facts", "maternal", "infant"],
    "beverages": ["beverages", "drinks", "coffee", "tea"],
    "chocolates": ["chocolates", "confectionery"],
    "frozen": ["frozen-meals", "frozen-desserts", "ice-cream"],
    "healthcare": ["healthcare", "health-science", "medical-nutrition"],
    "professional": ["professional", "food-service", "business-solutions"],
    "sustainability": ["sustainability", "planet", "environment", "responsible-sourcing"],
    "community": ["community", "communities", "charitable-partners", "nestle-cares"],
    "careers": ["careers", "jobs", "work-with-us"],
    "contact": ["contact", "contact-us", "support"]
}

# Known brand patterns with variations
BRAND_PATTERNS = {
    # Maternal and Infant Nutrition
    "GERBER": ["gerber", "gerber-baby", "gerber-graduates"],
    "MATERNA": ["materna"],
    "CERELAC": ["cerelac"],
    "NIDO": ["nido"],
    
    # Beverages
    "CARNATION": ["carnation", "carnation-hot-chocolate", "carnation-breakfast"],
    "MILO": ["milo"],
    "NESQUIK": ["nesquik"],
    "NESTEA": ["nestea"],
    "NESFRUTA": ["nesfruta"],
    "GOODHOST": ["goodhost", "good-host"],
    
    # Chocolates
    "AERO": ["aero"],
    "AFTER EIGHT": ["after-eight", "after_eight", "aftereight"],
    "BIG TURK": ["big-turk", "bigturk"],
    "COFFEE CRISP": ["coffee-crisp", "coffeecrisp"],
    "CRUNCH": ["crunch"],
    "KIT KAT": ["kitkat", "kit-kat", "kit_kat"],
    "MACKINTOSH TOFFEE": ["mackintosh-toffee", "mack-toffee", "macktoffee"],
    "MIRAGE": ["mirage"],
    "QUALITY STREET": ["quality-street", "quality_street", "qualitystreet"],
    "ROLO": ["rolo"],
    "SMARTIES": ["smarties"],
    "TURTLES": ["turtles"],
    
    # Coffee
    "COFFEE-MATE": ["coffee-mate", "coffeemate"],
    "NESCAFE": ["nescafe", "nescafé", "nescafe-dolce-gusto"],
    "NESPRESSO": ["nespresso"],
    
    # Frozen Meals
    "DELISSIO": ["delissio"],
    "LEAN CUISINE": ["lean-cuisine", "leancuisine"],
    "STOUFFER'S": ["stouffers", "stouffer", "stouffers-bistro"],
    
    # Nutrition and Health
    "BOOST": ["boost"],
    "IBGARD": ["ibgard"],
    "NATURE'S BOUNTY": ["natures-bounty", "naturesbounty"],
    
    # Ice Cream & Frozen Desserts
    "DEL MONTE": ["del-monte", "delmonte"],
    "DRUMSTICK": ["drumstick"],
    "HAAGEN-DAZS": ["haagen-dazs", "haagendazs"],
    "PARLOUR": ["parlour"],
    "REAL DAIRY": ["real-dairy", "realdairy"],
    
    # Imported Foods
    "MAGGI": ["maggi"],
    
    # Pet Foods
    "PURINA": ["purina"],
    
    # Waters
    "PERRIER": ["perrier"],
    "SAN PELLEGRINO": ["san-pellegrino", "sanpellegrino"],
    "ESSENTIA": ["essentia"]
}

def decode_url_part(text: str) -> str:
    """Decode URL-encoded text including hex sequences.
    
    Args:
        text (str): URL-encoded text
        
    Returns:
        str: Decoded text
    """
    # Handle hex-encoded characters (e.g., C3/A9 -> é)
    text = re.sub(r"C3/A9", "é", text, flags=re.IGNORECASE)
    text = re.sub(r"C3/A8", "è", text, flags=re.IGNORECASE)
    text = re.sub(r"C3/AB", "ë", text, flags=re.IGNORECASE)
    text = re.sub(r"C2/AE", "®", text, flags=re.IGNORECASE)
    
    # URL decode
    text = unquote(text)
    
    # HTML decode
    text = unescape(text)
    
    return text

def clean_title(text: str) -> str:
    """Clean and normalize title text.
    
    Args:
        text (str): Raw title text from URL
        
    Returns:
        str: Cleaned and normalized title
    """
    # Decode URL encoding
    text = decode_url_part(text)
    
    # Replace hyphens, underscores and extra spaces
    text = re.sub(r"[-_]", " ", text)
    text = re.sub(r"\s+", " ", text)
    
    # Remove numeric suffixes
    text = re.sub(r"\s*\d+$", "", text)
    
    # Capitalize words properly
    text = " ".join(word.capitalize() for word in text.split())
    
    # Fix brand capitalizations
    for brand, patterns in BRAND_PATTERNS.items():
        for pattern in patterns:
            text = re.sub(
                rf"\b{pattern}\b",
                brand,
                text,
                flags=re.IGNORECASE
            )
    
    return text.strip()

def extract_brand(path_parts: List[str]) -> Optional[str]:
    """Extract brand name from URL path parts.
    
    Args:
        path_parts (List[str]): Parts of the URL path
        
    Returns:
        Optional[str]: Extracted brand name if found
    """
    decoded_parts = [decode_url_part(part).lower() for part in path_parts]
    
    for brand, patterns in BRAND_PATTERNS.items():
        for part in decoded_parts:
            if any(pattern in part for pattern in patterns):
                return brand
    return None

def determine_content_type(path_parts: List[str], content: Optional[str] = None) -> str:
    """Determine content type from URL path and optionally content.
    
    Args:
        path_parts (List[str]): Parts of the URL path
        content (Optional[str]): Page content for fallback classification
        
    Returns:
        str: Determined content type
    """
    # Check first path component against known types
    if path_parts and path_parts[0]:
        first_part = decode_url_part(path_parts[0]).lower()
        for content_type, patterns in CONTENT_TYPES.items():
            if first_part in patterns:
                return content_type
    
    # Check if it's a brand page
    if extract_brand(path_parts):
        return "brand"
    
    # Fallback: analyze content if provided
    if content:
        content_lower = content.lower()
        if any(word in content_lower for word in ["recipe", "ingredients", "method", "preparation"]):
            return "recipe"
        if any(word in content_lower for word in ["news", "press release", "announced"]):
            return "news"
        if any(word in content_lower for word in ["about us", "our company", "our history"]):
            return "about"
    
    return "other"

def extract_keywords(url_parts: List[str], title: str, content_type: str, brand: Optional[str]) -> List[str]:
    """Extract relevant keywords from URL parts and metadata.
    
    Args:
        url_parts (List[str]): Parts of the URL path
        title (str): Normalized title
        content_type (str): Content type
        brand (Optional[str]): Brand name if available
        
    Returns:
        List[str]: List of relevant keywords
    """
    keywords = set()
    
    # Add content type
    keywords.add(content_type)
    
    # Add brand if available
    if brand:
        keywords.add(brand.lower())
    
    # Add meaningful words from title
    title_words = re.findall(r"\w+", title.lower())
    keywords.update(title_words)
    
    # Add meaningful parts from URL
    for part in url_parts:
        # Skip common structural parts
        if part.lower() in ["www", "com", "html", "php"]:
            continue
        # Skip numbers-only parts
        if part.isdigit():
            continue
        # Add decoded and cleaned part
        cleaned = decode_url_part(part).lower()
        keywords.update(re.findall(r"\w+", cleaned))
    
    # Remove common words and short terms
    stop_words = {"the", "and", "or", "in", "on", "at", "to", "for", "of", "with"}
    keywords = {k for k in keywords if len(k) > 2 and k not in stop_words}
    
    return sorted(list(keywords))

def parse_url(url: str, content: Optional[str] = None) -> Dict:
    """Parse URL and extract structured information.
    
    Args:
        url (str): URL to parse
        content (Optional[str]): Page content for better classification
        
    Returns:
        Dict: Structured information extracted from URL
    """
    try:
        # Parse URL
        parsed = urlparse(url)
        
        # Split path into parts and remove empty strings
        path_parts = [p for p in parsed.path.split("/") if p]
        
        # Extract information
        content_type = determine_content_type(path_parts, content)
        brand = extract_brand(path_parts)
        
        # Generate normalized title from the last meaningful path part
        title_source = path_parts[-1] if path_parts else ""
        if title_source.isdigit() and len(path_parts) > 1:
            title_source = path_parts[-2]
        normalized_title = clean_title(title_source)
        
        # Extract keywords
        keywords = extract_keywords(path_parts, normalized_title, content_type, brand)
        
        return {
            "content_type": content_type,
            "brand": brand,
            "normalized_title": normalized_title,
            "keywords": keywords,
            "original_url": url
        }
        
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {str(e)}")
        return {
            "content_type": "other",
            "brand": None,
            "normalized_title": "",
            "keywords": [],
            "original_url": url
        } 