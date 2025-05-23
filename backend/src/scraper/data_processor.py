import os
import json
import re
import urllib.parse
from typing import Dict, List, Set, Tuple
from datetime import datetime
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from collections import defaultdict, Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams

from .url_parser import parse_url


# Download required NLTK data if not already present
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("tokenizers/punkt_tab")
    nltk.data.find("corpora/stopwords")
except LookupError:
    print("Downloading required NLTK data...")
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
    nltk.download("stopwords", quiet=True)

# Common food-related compound terms that should be kept together
FOOD_COMPOUND_TERMS = [
    # Ice cream and frozen desserts
    "ice cream", "ice creams", "soft serve", "hard pack", "gelato", "sorbet",
    "frozen yogurt", "frozen dessert", "frozen desserts", "ice cream cake",
    "ice cream sandwich", "ice cream cone", "ice cream bar", "ice cream sundae",
    "vanilla ice cream", "chocolate ice cream", "strawberry ice cream",
    
    # Chocolate varieties  
    "milk chocolate", "dark chocolate", "white chocolate", "chocolate chip",
    "chocolate chips", "chocolate bar", "chocolate bars", "chocolate cake",
    "chocolate mousse", "chocolate sauce", "chocolate syrup", "hot chocolate",
    "chocolate brownie", "chocolate cookie", "chocolate cookies",
    
    # Coffee products
    "instant coffee", "ground coffee", "coffee beans", "coffee machine",
    "coffee maker", "coffee shop", "iced coffee", "cold brew", "espresso",
    "cappuccino", "latte", "macchiato", "coffee crisp", "coffee mate",
    
    # Cream and dairy
    "whipped cream", "heavy cream", "light cream", "sour cream", "cream cheese",
    "real dairy", "dairy free", "non dairy",
    
    # Baking ingredients
    "baking powder", "baking soda", "vanilla extract", "almond extract",
    "brown sugar", "powdered sugar", "maple syrup", "corn syrup", 
    "coconut oil", "olive oil", "vegetable oil",
    
    # Recipe terms
    "prep time", "cook time", "total time", "serving size", "recipe card",
    "step by step", "easy recipe", "quick recipe", "healthy recipe",
    
    # Nutrition terms
    "calorie count", "nutrition facts", "dietary fiber", "saturated fat",
    "trans fat", "vitamin c", "vitamin d", "vitamin b", "omega 3",
    
    # Meal types
    "breakfast cereal", "lunch box", "dinner party", "snack time",
    "meal planning", "meal prep", "family dinner", "quick meal",
    
    # Cooking methods
    "slow cooker", "pressure cooker", "air fryer", "food processor",
    "stand mixer", "hand mixer", "baking sheet", "mixing bowl",
    
    # Product categories
    "frozen meals", "ready meals", "baby food", "pet food", "health food",
    "organic food", "gluten free", "sugar free", "fat free", "low fat"
]

# Brand compound terms
BRAND_COMPOUND_TERMS = [
    "kit kat", "quality street", "after eight", "coffee crisp", "big turk",
    "lean cuisine", "haagen dazs", "del monte", "real dairy", "coffee mate",
    "natures bounty", "san pellegrino"
]

# All compound terms combined
ALL_COMPOUND_TERMS = FOOD_COMPOUND_TERMS + BRAND_COMPOUND_TERMS

# Common boilerplate content patterns to exclude
EXCLUDE_SECTION_PATTERNS = [
    r"information we collect about you",
    r"performance cookies",
    r"cookie policy",
    r"privacy policy",
    r"terms of service",
    r"terms and conditions",
    r"cookie settings",
    r"manage cookies",
    r"privacy notice",
    r"data protection",
    r"gdpr",
    r"legal notice",
    r"copyright notice",
    r"all rights reserved",
    r"newsletter signup",
    r"follow us",
    r"social media",
    r"share this",
    r"share on facebook",
    r"share on twitter", 
    r"share on pinterest",
    r"facebook.*twitter.*pinterest",
    r"skip to main content",
    r"contact us",
    r"customer service",
    r"site map",
    r"help center",
    r"accessibility",
    r"modern slavery statement"
]

# Minimum content length to consider (filter out very short sections)
MIN_CONTENT_LENGTH = 50

def extract_compound_phrases(text: str) -> List[str]:
    """
    Extract compound phrases from text using predefined compound terms.
    
    Args:
        text (str): Input text to analyze
        
    Returns:
        List[str]: List of compound phrases found in text
    """
    text_lower = text.lower()
    found_phrases = []
    
    # Sort by length (longest first) to catch longer phrases first
    sorted_compounds = sorted(ALL_COMPOUND_TERMS, key=len, reverse=True)
    
    for compound in sorted_compounds:
        if compound in text_lower:
            found_phrases.append(compound)
            # Replace found phrase with placeholder to avoid overlapping matches
            text_lower = text_lower.replace(compound, f"_COMPOUND_{len(found_phrases)}_")
    
    return found_phrases

def extract_meaningful_ngrams(text: str, n_range: Tuple[int, int] = (2, 3)) -> List[str]:
    """
    Extract meaningful n-grams from text using NLTK if available, fallback to basic method.
    
    Args:
        text (str): Input text
        n_range (Tuple[int, int]): Range of n-gram sizes (min, max)
        
    Returns:
        List[str]: List of meaningful n-grams
    """
    # Enhanced method with NLTK
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english"))
    
    # Filter out stopwords, punctuation, and very short words
    filtered_tokens = [
        token for token in tokens 
        if token.isalpha() and len(token) > 2 and token not in stop_words
    ]
    
    if len(filtered_tokens) < n_range[0]:
        return []
    
    meaningful_ngrams = []
    
    # Extract n-grams of different sizes
    for n in range(n_range[0], min(n_range[1] + 1, len(filtered_tokens) + 1)):
        n_grams = list(ngrams(filtered_tokens, n))
        
        for gram in n_grams:
            phrase = " ".join(gram)
            
            # Only keep n-grams that look like meaningful phrases
            if is_food_related_phrase(phrase):
                meaningful_ngrams.append(phrase)
    
    return meaningful_ngrams[:10]  # Limit to top 10

def is_food_related_phrase(phrase: str) -> bool:
    """
    Check if a phrase is meaningful for food/recipe context.
    
    Args:
        phrase (str): Phrase to check
        
    Returns:
        bool: True if phrase seems meaningful
    """
    # Food-related keywords that indicate a meaningful phrase
    food_indicators = [
        "chocolate", "cream", "ice", "coffee", "recipe", "baking", "cooking",
        "dessert", "cake", "cookie", "sweet", "flavor", "ingredient", "sauce",
        "syrup", "butter", "sugar", "vanilla", "caramel", "strawberry", "berry",
        "fruit", "nut", "almond", "coconut", "lemon", "orange", "mint", "crispy",
        "smooth", "rich", "delicious", "frozen", "fresh", "organic", "natural"
    ]
    
    # Check if phrase contains food-related terms
    phrase_words = phrase.split()
    has_food_term = any(word in food_indicators for word in phrase_words)
    
    # Avoid generic phrases
    generic_terms = ["new", "great", "good", "best", "more", "other", "all", "some"]
    is_generic = all(word in generic_terms for word in phrase_words)
    
    return has_food_term and not is_generic and len(phrase_words) <= 4

def keyword_extraction(url_parts: List[str], title: str, content: str, 
                               content_type: str, brand: str = None) -> List[str]:
    """
    Keyword extraction that preserves compound terms and extracts meaningful phrases.
    
    Args:
        url_parts (List[str]): URL path parts
        title (str): Page title
        content (str): Full page content
        content_type (str): Content type
        brand (str): Brand name if available
        
    Returns:
        List[str]: List of keywords including compound terms
    """
    keywords = set()
    
    # Add content type and brand
    keywords.add(content_type)
    if brand:
        keywords.add(brand.lower())
    
    # Combine all text for analysis
    all_text = f"{title} {' '.join(url_parts)} {content}"
    
    # Extract keywords
    compound_phrases = extract_compound_phrases(all_text)
    keywords.update(compound_phrases)
    meaningful_phrases = extract_meaningful_ngrams(all_text, n_range=(2, 3))
    keywords.update(meaningful_phrases)
    title_words = re.findall(r"\w+", title.lower())
    keywords.update([word for word in title_words if len(word) > 2])
    
    # Add meaningful parts from URL
    for part in url_parts:
        if part.lower() not in ["www", "com", "html", "php"] and not part.isdigit():
            cleaned = urllib.parse.unquote(part).lower()
            # Check for compound terms in URL parts
            if cleaned.replace("-", " ") in ALL_COMPOUND_TERMS:
                keywords.add(cleaned.replace("-", " "))
            else:
                keywords.update(re.findall(r"\w+", cleaned))
    
    # Extract keywords from content with better context awareness
    if content:
        content_keywords = extract_content_keywords(content)
        keywords.update(content_keywords)
    
    # Remove stop words and very short terms
    stop_words = {"the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "a", "an"}
    keywords = {k for k in keywords if len(k) > 2 and k not in stop_words}
    
    return sorted(list(keywords))

def extract_content_keywords(content: str, max_keywords: int = 20) -> List[str]:
    """
    Extract meaningful keywords from content using frequency analysis and compound detection.
    
    Args:
        content (str): Page content
        max_keywords (int): Maximum number of keywords to return
        
    Returns:
        List[str]: List of meaningful keywords
    """
    keywords = set()
    
    # Extract compound phrases from content
    compound_phrases = extract_compound_phrases(content)
    keywords.update(compound_phrases)
    
    # Extract individual words with frequency analysis
    words = re.findall(r"\b\w{3,}\b", content.lower())
    word_freq = Counter(words)
    
    # Get English stop words
    stop_words = set(stopwords.words("english"))
    
    # Filter words by relevance and frequency
    food_related_words = []
    
    for word, freq in word_freq.most_common(50):  # Look at top 50 words
        if (word not in stop_words and 
            freq >= 2 and  # Appears at least twice
            (is_food_related_word(word) or freq >= 5)):  # Either food-related or very frequent
            food_related_words.append(word)
    
    keywords.update(food_related_words[:max_keywords])
    
    return list(keywords)

def is_food_related_word(word: str) -> bool:
    """
    Check if a word is related to food, cooking, or nutrition.
    
    Args:
        word (str): Word to check
        
    Returns:
        bool: True if word is food-related
    """
    food_domains = [
        # Ingredients
        "chocolate", "vanilla", "strawberry", "caramel", "coconut", "almond", "peanut",
        "butter", "cream", "milk", "sugar", "honey", "maple", "cinnamon", "mint",
        
        # Food types
        "cookie", "cake", "pie", "bread", "pasta", "sauce", "soup", "salad",
        "sandwich", "pizza", "burger", "cereal", "yogurt", "cheese", "fruit",
        
        # Cooking terms
        "recipe", "baking", "cooking", "grilling", "frying", "boiling", "mixing",
        "seasoning", "marinating", "sautéing", "roasting", "preparation",
        
        # Descriptors
        "crispy", "creamy", "sweet", "salty", "spicy", "fresh", "frozen", "organic",
        "delicious", "tasty", "flavorful", "rich", "smooth", "crunchy",
        
        # Nutrition
        "calories", "protein", "fiber", "vitamins", "minerals", "healthy", "nutrition",
        "ingredients", "serving", "portion"
    ]
    
    return word in food_domains

def sanitize_url(url: str) -> str:
    """
    Sanitize URL for safe storage and retrieval.
    
    Args:
        url (str): Raw URL
        
    Returns:
        str: Sanitized URL safe for storage
    """
    # Decode URL-encoded characters
    decoded = urllib.parse.unquote(url)
    
    # Remove any protocol prefix
    decoded = re.sub(r'^https?://', '', decoded)
    
    # Remove special characters and spaces
    sanitized = re.sub(r'[^a-zA-Z0-9\-_/]', '_', decoded)
    
    # Replace multiple underscores with single one
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    return sanitized

def generate_safe_id(url: str, doc_index: int, chunk_index: int) -> str:
    """
    Generate a safe document ID from URL and indices.
    
    Args:
        url (str): Document URL
        doc_index (int): Document index
        chunk_index (int): Chunk index
        
    Returns:
        str: Safe document ID
    """
    safe_url = sanitize_url(url)
    return f"{safe_url}_{doc_index}_{chunk_index}"

def is_error_page(title: str) -> bool:
    """
    Check if a page is an error page (404, 500, etc.).
    
    Args:
        title (str): Page title
        
    Returns:
        bool: True if page is an error page
    """
    title_lower = title.lower() if title else ""
    
    error_indicators = [
        "404 error",
        "page not found",
        "page doesn't exist",
        "page has been removed",
        "red mugger strikes",
        "stole the page you were looking for"
    ]
    
    for indicator in error_indicators:
        if indicator in title_lower:
            return True
    
    error_codes = ["400", "401", "403", "404", "500", "502", "503"]
    for code in error_codes:
        if code in title_lower:
            return True
    
    return False

def is_boilerplate_section(title: str, content: str) -> bool:
    """
    Check if a section is likely boilerplate content (cookies, privacy, etc.).
    
    Args:
        title (str): Section title
        content (str): Section content
        
    Returns:
        bool: True if section should be excluded
    """
    if not title and not content:
        return True
        
    # Check if content is too short
    if len(content.strip()) < MIN_CONTENT_LENGTH:
        return True
    
    # Check if this is an error page
    if is_error_page(title):
        return True
    
    # Check title against exclusion patterns
    title_lower = title.lower() if title else ""
    content_lower = content.lower()
    
    for pattern in EXCLUDE_SECTION_PATTERNS:
        if re.search(pattern, title_lower) or re.search(pattern, content_lower):
            return True
    
    # Check for social media sharing sections
    social_media_indicators = [
        "facebook", "twitter", "pinterest", "email", "yummly", "instagram", "linkedin"
    ]
    social_link_count = sum(1 for platform in social_media_indicators if platform in content_lower)
    if social_link_count >= 3 and any(term in content_lower for term in ["share", "follow", "connect"]):
        return True
    
    # More careful detection for web cookies vs food cookies
    web_cookie_indicators = [
        "tracking", "analytics", "advertising", "gdpr", "consent", 
        "privacy policy", "data protection", "personal information",
        "third party", "performance cookies", "functional cookies",
        "targeting cookies", "essential cookies", "browser",
        "website", "collect information", "your preferences",
        "opt out", "manage cookies", "cookie settings"
    ]
    
    food_cookie_indicators = [
        "recipe", "ingredients", "chocolate", "baking", "oven",
        "flour", "sugar", "butter", "vanilla", "cream",
        "crispy", "chewy", "sweet", "dessert", "treat"
    ]
    
    # If "cookie" appears, check context to determine if it's web or food related
    if "cookie" in content_lower:
        web_score = sum(1 for indicator in web_cookie_indicators if indicator in content_lower)
        food_score = sum(1 for indicator in food_cookie_indicators if indicator in content_lower)
        
        # Only filter as web cookie content if:
        # 1. Multiple web indicators present AND
        # 2. No food indicators OR web indicators significantly outweigh food indicators
        if web_score >= 2 and (food_score == 0 or web_score > food_score * 2):
            return True
    
    # Check for navigation-only content
    nav_patterns = [
        r"^(home|about|contact|products|services|blog)$",
        r"^\s*>\s*",  # Breadcrumb navigation
        r"^[<>←→\s]+$"  # Navigation arrows/symbols
    ]
    
    for pattern in nav_patterns:
        if re.match(pattern, content.strip(), re.IGNORECASE):
            return True
    
    return False

def is_common_content(content: str, common_hashes: Set[str]) -> bool:
    """
    Check if content matches common/boilerplate content.
    
    Args:
        content (str): Content to check
        common_hashes (Set[str]): Set of common content hashes
        
    Returns:
        bool: True if content is common boilerplate
    """
    normalized = re.sub(r'\s+', ' ', content.lower().strip())
    content_hash = hash(normalized)
    return content_hash in common_hashes

def validate_markdown_file(file_path: str) -> bool:
    """
    Validate a markdown file exists and has content.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return len(content) > 0
    except Exception:
        return False

def detect_common_content(content_dir: str) -> Set[str]:
    """
    Detect content that appears across multiple pages (likely boilerplate).
    
    Args:
        content_dir (str): Directory containing markdown files
        
    Returns:
        Set[str]: Set of content hashes that appear frequently
    """
    content_frequency = defaultdict(int)
    total_files = 0
    
    print("Analyzing content for common sections...")
    
    for filename in os.listdir(content_dir):
        if not filename.endswith(".md"):
            continue
            
        file_path = os.path.join(content_dir, filename)
        try:
            content = read_markdown_file(file_path)
            
            # Split into sections and hash each one
            sections = re.split(r'\n#{1,6}\s+', content)
            for section in sections:
                section = section.strip()
                if len(section) > MIN_CONTENT_LENGTH:
                    # Create a normalized hash of the section
                    normalized = re.sub(r'\s+', ' ', section.lower())
                    section_hash = hash(normalized)
                    content_frequency[section_hash] += 1
            
            total_files += 1
            
        except Exception as e:
            print(f"Error analyzing {filename}: {str(e)}")
    
    # Consider content "common" if it appears in more than 30% of files
    threshold = max(2, total_files * 0.3)
    common_content = {h for h, freq in content_frequency.items() if freq >= threshold}
    
    print(f"Found {len(common_content)} common content sections appearing in {threshold}+ files")
    return common_content

def remove_content_duplicates(raw_dir: str = None) -> Dict:
    """
    Find and remove files with duplicate content, keeping only one copy.
    
    Args:
        raw_dir (str): Path to directory containing raw markdown files
        
    Returns:
        Dict: Report of duplicate files and actions taken
    """
    # Track content hashes and their files
    content_map = defaultdict(list)
    
    # Collect all files and their content hashes
    print("Scanning files...")
    for filename in os.listdir(raw_dir):
        if not filename.endswith(".md"):
            continue
            
        file_path = os.path.join(raw_dir, filename)
        try:
            content = read_markdown_file(file_path)
            content_hash = hash(content.lower().replace(" ", ""))
            content_map[content_hash].append({
                "filename": filename,
                "path": file_path,
                "url": filename[:-3].replace("_", "/"),
                "size": os.path.getsize(file_path)
            })
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            
    # Find and handle duplicates
    duplicates = {
        h: files for h, files in content_map.items()
        if len(files) > 1
    }
    
    if not duplicates:
        return {
            "status": "success",
            "message": "No duplicate content found",
            "duplicates": {}
        }
        
    # Process duplicates
    results = {
        "status": "success",
        "message": f"Found {len(duplicates)} sets of duplicate content",
        "duplicates": {}
    }
    
    for content_hash, files in duplicates.items():
        # Sort by URL complexity (fewer slashes = simpler URL)
        files.sort(key=lambda x: x["url"].count("/"))
        
        # Keep the file with the simplest URL
        keep = files[0]
        remove = files[1:]
        
        # Record the duplicates
        results["duplicates"][keep["url"]] = {
            "kept": keep["filename"],
            "removed": [f["filename"] for f in remove]
        }
        
        # Remove duplicate files
        for file in remove:
            try:
                os.remove(file["path"])
                print(f"Removed duplicate file: {file['filename']}")
            except Exception as e:
                print(f"Error removing {file['filename']}: {str(e)}")
                
    return results 

def read_markdown_file(file_path: str) -> str:
    """
    Read and return the content of a markdown file.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        str: Content of the file
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def process_markdown_file(file_path: str, url: str, common_content_hashes: Set[str]) -> List[Dict]:
    """
    Process a markdown file into chunks using LangChain's text splitters.
    
    Args:
        file_path (str): Path to the markdown file
        url (str): Original URL of the content
        common_content_hashes (Set[str]): Set of common content hashes to exclude
        
    Returns:
        List[Dict]: List of chunks
    """
    content = read_markdown_file(file_path)
    
    # Parse URL for basic metadata
    url_info = parse_url(url, content)
    
    # Check if entire page is an error page - skip if so
    if is_error_page(url_info["normalized_title"]):
        print(f"Skipping error page: {url}")
        return []
    
    # Keyword extraction that includes compound terms
    url_parts = [p for p in url.split("/") if p and p not in ["http:", "https:", ""]]
    keywords = keyword_extraction(
        url_parts, 
        url_info["normalized_title"], 
        content,
        url_info["content_type"], 
        url_info["brand"]
    )
    
    # Override keywords
    url_info["keywords"] = keywords
    
    # Override content type for special cases
    if url.startswith("#") or url.startswith("javascript:"):
        url_info["content_type"] = "navigation"
        url_info["keywords"] = ["navigation"]
    elif "recipe" in url_info["content_type"] and not any(
        keyword in content.lower() 
        for keyword in ["ingredients", "preparation", "method", "directions", "recipe", "cooking"]
    ):
        url_info["content_type"] = "other"
        url_info["keywords"] = [k for k in url_info["keywords"] if k != "recipe"]
    
    # First split on markdown headers to preserve document structure
    markdown_splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=200)
    markdown_docs = markdown_splitter.create_documents([content])
    
    # Further split large sections if needed
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    safe_url = sanitize_url(url)
    filtered_sections = 0
    
    for doc_idx, doc in enumerate(markdown_docs):
        # Look for headers in the content
        lines = doc.page_content.split("\n")
        title = None
        
        # Try to find a header line
        for line in lines:
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
        
        # If no header found, use first sentence as title
        if not title:
            content_text = " ".join(lines).strip()
            sentence_end = content_text.find(".")
            if sentence_end > 0 and sentence_end < 100:
                title = content_text[:sentence_end].strip()
            else:
                title = content_text[:50].strip() + "..."
        
        # Check if this section should be filtered out
        if is_boilerplate_section(title, doc.page_content):
            filtered_sections += 1
            continue
            
        # Check if this is common content across many pages
        if is_common_content(doc.page_content, common_content_hashes):
            filtered_sections += 1
            continue
        
        # Split into smaller chunks if needed
        if len(doc.page_content) > 1000:
            section_chunks = text_splitter.split_text(doc.page_content)
        else:
            section_chunks = [doc.page_content]
            
        for chunk_idx, chunk in enumerate(section_chunks):
            # Final check - skip if chunk is too short or looks like boilerplate
            if len(chunk.strip()) < MIN_CONTENT_LENGTH:
                continue
            
            # Extract chunk-specific keywords including compound phrases
            chunk_keywords = extract_content_keywords(chunk, max_keywords=10)
            
            # Combine page-level and chunk-level keywords
            all_keywords = list(set(keywords + chunk_keywords))
                
            chunks.append({
                "id": generate_safe_id(url, doc_idx, chunk_idx),
                "url": safe_url,
                "content_type": url_info["content_type"],
                "brand": url_info["brand"],
                "page_title": url_info["normalized_title"],
                "section_title": title,
                "keywords": all_keywords,
                "doc_index": doc_idx,
                "chunk_index": chunk_idx,
                "total_chunks": len(section_chunks),
                "content": chunk.strip(),
                "processed_at": datetime.utcnow().isoformat()
            })
    
    if filtered_sections > 0:
        print(f"Filtered {filtered_sections} boilerplate sections from {url}")
    
    return chunks

def process_all_content(raw_dir: str = None, processed_dir: str = None) -> Dict:
    """
    Process all markdown files and prepare them for vector storage.
    
    Args:
        raw_dir (str): Path to directory containing raw markdown files
        processed_dir (str): Path to directory for processed output files
        
    Returns:
        Dict: Processing results and statistics
    """
    # First pass: detect common content across all files
    common_content_hashes = detect_common_content(raw_dir)
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_files": 0,
        "total_chunks": 0,
        "filtered_sections": 0,
        "content_types": defaultdict(int),
        "brands": defaultdict(int),
        "files": []
    }
    
    all_chunks = []
    
    print("Processing files...")
    
    for filename in os.listdir(raw_dir):
        if not filename.endswith(".md"):
            continue
            
        file_path = os.path.join(raw_dir, filename)
        url = filename[:-3].replace("_", "/")
        
        try:
            chunks = process_markdown_file(file_path, url, common_content_hashes)
            all_chunks.extend(chunks)
            
            # Update statistics
            if chunks:
                first_chunk = chunks[0]
                results["content_types"][first_chunk["content_type"]] += 1
                if first_chunk["brand"]:
                    results["brands"][first_chunk["brand"]] += 1
            
            file_info = {
                "filename": filename,
                "url": sanitize_url(url),
                "chunks": len(chunks),
                "content_type": chunks[0]["content_type"] if chunks else "unknown",
                "brand": chunks[0]["brand"] if chunks else None,
                "title": chunks[0]["page_title"] if chunks else None,
                "status": "success"
            }
            results["files"].append(file_info)
            results["total_chunks"] += len(chunks)
            results["total_files"] += 1
            
        except Exception as e:
            results["files"].append({
                "filename": filename,
                "url": sanitize_url(url),
                "status": "error",
                "error": str(e)
            })
    
    # Save all chunks to a single file
    chunks_file = os.path.join(processed_dir, "vector_chunks.json")
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Convert defaultdict to regular dict for JSON serialization
    results["content_types"] = dict(results["content_types"])
    results["brands"] = dict(results["brands"])
    
    # Save processing results
    results_file = os.path.join(processed_dir, "processing_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {results['total_files']} files into {results['total_chunks']} chunks")
    print("✅ Keywords now preserve compound terms like 'ice cream', 'chocolate chip', etc.")
    
    return results