import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, urljoin
from urllib.parse import unquote, urlparse
from html import unescape

from config.content_types import CONTENT_TYPES, CONTENT_TYPE_KEYWORDS
from config.brands import BRAND_PATTERNS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    # Check for brand page structure
    if len(path_parts) == 1:
        first_part = decode_url_part(path_parts[0]).lower()
        # Check if this single part matches any brand pattern
        for brand, patterns in BRAND_PATTERNS.items():
            if any(pattern.lower() == first_part for pattern in patterns):
                return "brand"
    
    # Check for product page structure
    if len(path_parts) >= 2:
        first_part = decode_url_part(path_parts[0]).lower()
        # Check if first part matches any brand pattern
        for brand, patterns in BRAND_PATTERNS.items():
            if any(pattern.lower() == first_part for pattern in patterns):
                return "product"
    
    # Check first path component against known content type patterns
    if path_parts and path_parts[0]:
        first_part = decode_url_part(path_parts[0]).lower()
        for content_type, patterns in CONTENT_TYPES.items():
            if first_part in patterns:
                return content_type
    
    # Content analysis fallback
    if content:
        content_lower = content.lower()
        
        # Score each content type based on keyword matches
        type_scores = {}
        for content_type, keywords in CONTENT_TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                type_scores[content_type] = score
        
        # Return the content type with the highest score
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1])[0]
            return best_type
    
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
    
    # Import our minimal technical stop words
    from config.scraper import STOP_WORDS
    
    # Remove only technical terms and short terms
    keywords = {k for k in keywords if len(k) > 2 and k not in STOP_WORDS}
    
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