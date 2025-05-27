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
from .llm_keyword_extractor import extract_keywords_with_llm
from .keyword_utils import is_meaningful_keyword
from backend.config import (
    # Compound terms
    ALL_COMPOUND_TERMS,
    
    # Content filtering
    EXCLUDE_SECTION_PATTERNS,
    MIN_CONTENT_LENGTH,
    FOOD_INDICATORS,
    GENERIC_TERMS,
    STOP_WORDS,
    
    # Classification indicators
    WEB_COOKIE_INDICATORS,
    FOOD_COOKIE_INDICATORS,
    SOCIAL_MEDIA_INDICATORS,
    FOOD_DOMAINS,
    ERROR_INDICATORS,
    
    # Enhanced filtering patterns
    CONSENT_MANAGEMENT_PATTERNS,
    PRIVACY_CONTENT_INDICATORS,
    
    # Processing settings
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    MARKDOWN_CHUNK_SIZE,
    MARKDOWN_CHUNK_OVERLAP,
    MAX_KEYWORDS_PER_CHUNK,
    NGRAM_RANGE,
    MAX_NGRAMS,
    MAX_PHRASE_LENGTH,
)

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

# All constants now imported from centralized configuration

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

def contains_unwanted_terms(phrase: str) -> bool:
    """
    Check if a phrase contains unwanted terms like social media, web terms, etc.
    
    Args:
        phrase (str): Phrase to check
        
    Returns:
        bool: True if phrase contains unwanted terms
    """
    phrase_lower = phrase.lower()
    
    # Check for social media terms
    for term in SOCIAL_MEDIA_INDICATORS:
        if term in phrase_lower:
            return True
    
    # Check for web-related fragments
    web_fragments = ['https', 'http', 'www', '.com', '.ca', '.org', 'sauce https']
    for fragment in web_fragments:
        if fragment in phrase_lower:
            return True
    
    # Check for common unwanted phrase patterns
    unwanted_patterns = [
        'behind delicious', 'keep exploring', 'measure impact', 'proud partner',
        'delighted consumers', 'years'
    ]
    for pattern in unwanted_patterns:
        if pattern in phrase_lower:
            return True
    
    return False

def extract_meaningful_ngrams(text: str, n_range: Tuple[int, int] = NGRAM_RANGE) -> List[str]:
    """
    Extract meaningful n-grams from text using NLTK with minimal filtering.
    
    Args:
        text (str): Input text
        n_range (Tuple[int, int]): Range of n-gram sizes (min, max)
        
    Returns:
        List[str]: List of meaningful n-grams
    """
    # Enhanced method with NLTK
    tokens = word_tokenize(text.lower())
    
    filtered_tokens = [
        token for token in tokens 
        if (token.isalpha() and 
            len(token) > 2 and 
            token not in STOP_WORDS and
            is_meaningful_keyword(token))
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
            if is_food_related_phrase(phrase) and not contains_unwanted_terms(phrase):
                meaningful_ngrams.append(phrase)
    
    return meaningful_ngrams[:MAX_NGRAMS]  # Limit to configured max

def is_food_related_phrase(phrase: str) -> bool:
    """
    Check if a phrase is meaningful for food/recipe context.
    
    Args:
        phrase (str): Phrase to check
        
    Returns:
        bool: True if phrase seems meaningful
    """
    # Check if phrase contains food-related terms (using centralized config)
    phrase_words = phrase.split()
    has_food_term = any(word in FOOD_INDICATORS for word in phrase_words)
    
    # Avoid generic phrases (using centralized config)
    is_generic = all(word in GENERIC_TERMS for word in phrase_words)
    
    return has_food_term and not is_generic and len(phrase_words) <= MAX_PHRASE_LENGTH



def keyword_extraction(url_parts: List[str], title: str, content: str, 
                               content_type: str, brand: str = None) -> List[str]:
    """
    Keyword extraction using LLM with fallback to rule-based approach.
    
    Args:
        url_parts (List[str]): URL path parts
        title (str): Page title
        content (str): Full page content
        content_type (str): Content type
        brand (str): Brand name if available
        
    Returns:
        List[str]: List of meaningful keywords
    """
    try:
        # Use LLM-based keyword extraction
        keywords = extract_keywords_with_llm(content, title, content_type, brand)
        
        # If LLM returns good results, use them
        if len(keywords) >= 3:
            return keywords
        
        # Otherwise fall back to basic rule-based extraction
        return _fallback_keyword_extraction(url_parts, title, content, content_type, brand)
        
    except Exception as e:
        print(f"Keyword extraction failed, using fallback: {e}")
        return _fallback_keyword_extraction(url_parts, title, content, content_type, brand)

def _fallback_keyword_extraction(url_parts: List[str], title: str, content: str, 
                                content_type: str, brand: str = None) -> List[str]:
    """
    Fallback rule-based keyword extraction.
    
    Args:
        url_parts (List[str]): URL path parts
        title (str): Page title
        content (str): Full page content
        content_type (str): Content type
        brand (str): Brand name if available
        
    Returns:
        List[str]: List of keywords
    """
    keywords = set()
    
    # Add content type and brand
    keywords.add(content_type)
    if brand:
        keywords.add(brand.lower())
    
    # Extract meaningful words from title
    title_words = re.findall(r"\w+", title.lower())
    for word in title_words:
        if len(word) > 2 and is_meaningful_keyword(word):
            keywords.add(word)
    
    # Add meaningful parts from URL
    for part in url_parts:
        if part.lower() not in ["www", "com", "html", "php", "http", "https"] and not part.isdigit():
            cleaned = urllib.parse.unquote(part).lower()
            # Check for compound terms in URL parts
            if cleaned.replace("-", " ") in ALL_COMPOUND_TERMS:
                keywords.add(cleaned.replace("-", " "))
            else:
                # Extract words from URL part and filter them
                url_words = re.findall(r"\w+", cleaned)
                for word in url_words:
                    if len(word) > 2 and is_meaningful_keyword(word):
                        keywords.add(word)
    
    # Basic content analysis for food-related terms
    if content:
        # Look for food-related terms in content
        content_lower = content.lower()
        for food_term in FOOD_INDICATORS:
            if food_term in content_lower:
                keywords.add(food_term)
    
    # Final filtering and limit
    filtered_keywords = [k for k in keywords if is_meaningful_keyword(k)]
    return sorted(filtered_keywords[:10])  # Limit to 10 keywords

def extract_content_keywords(content: str, max_keywords: int = MAX_KEYWORDS_PER_CHUNK) -> List[str]:
    """
    Extract meaningful keywords from content using LLM with fallback to frequency analysis.
    
    Args:
        content (str): Page content
        max_keywords (int): Maximum number of keywords to return
        
    Returns:
        List[str]: List of meaningful keywords
    """
    # Try LLM-based extraction for chunks if content is substantial
    if len(content) > 100:
        try:
            # Use LLM for chunk-level keyword extraction
            chunk_title = content[:100] + "..." if len(content) > 100 else content
            llm_keywords = extract_keywords_with_llm(content, chunk_title, "content", None)
            
            # Filter out content type and focus on meaningful terms
            filtered_keywords = [k for k in llm_keywords if k not in ["content", "product", "brand"]]
            
            if len(filtered_keywords) >= 3:
                return filtered_keywords[:max_keywords]
        except Exception as e:
            print(f"LLM chunk keyword extraction failed: {e}")
    
    # Fallback to basic frequency analysis
    return _fallback_content_keywords(content, max_keywords)

def _fallback_content_keywords(content: str, max_keywords: int = MAX_KEYWORDS_PER_CHUNK) -> List[str]:
    """
    Fallback content keyword extraction using frequency analysis.
    
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
    
    # Filter words by relevance and frequency
    meaningful_words = []
    
    for word, freq in word_freq.most_common(20):
        if (word not in STOP_WORDS and
            freq >= 2 and
            is_meaningful_keyword(word) and
            (is_food_related_word(word) or freq >= 3)):
            meaningful_words.append(word)
    
    keywords.update(meaningful_words[:max_keywords])
    
    return list(keywords)

def is_food_related_word(word: str) -> bool:
    """
    Check if a word is related to food, cooking, or nutrition.
    
    Args:
        word (str): Word to check
        
    Returns:
        bool: True if word is food-related
    """
    return word in FOOD_DOMAINS

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
    
    # Check against centralized error indicators
    for indicator in ERROR_INDICATORS:
        if indicator in title_lower:
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
    
    # Filter boilerplate patterns
    title_lower = title.lower() if title else ""
    content_lower = content.lower()
    for pattern in EXCLUDE_SECTION_PATTERNS:
        if re.search(pattern, title_lower) or re.search(pattern, content_lower):
            return True
    
    # Filter social media sharing sections
    social_link_count = sum(1 for platform in SOCIAL_MEDIA_INDICATORS if platform in content_lower)
    if social_link_count >= 3 and any(term in content_lower for term in ["share", "follow", "connect"]):
        return True
    
    # Filter web-related cookies with enhanced logic
    if "cookie" in content_lower or "consent" in content_lower or "privacy" in content_lower:
        web_score = sum(1 for indicator in WEB_COOKIE_INDICATORS if indicator in content_lower)
        food_score = sum(1 for indicator in FOOD_COOKIE_INDICATORS if indicator in content_lower)
        
        # More sensitive filtering - lower threshold and additional patterns
        if web_score >= 1 and food_score == 0:
            return True
        
        # Additional check for common consent management patterns
        consent_score = sum(1 for pattern in CONSENT_MANAGEMENT_PATTERNS if pattern in content_lower)
        if consent_score >= 1:
            return True
    
    # Additional quick check for obvious privacy/cookie content
    if any(indicator in content_lower for indicator in PRIVACY_CONTENT_INDICATORS):
        return True
    
    return False

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

def process_markdown_file(file_path: str, url: str) -> List[Dict]:
    """
    Process a markdown file into chunks using LangChain's text splitters.
    
    Args:
        file_path (str): Path to the markdown file
        url (str): Original URL of the content
        
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
    
    # First split on markdown headers to preserve document structure (using centralized config)
    markdown_splitter = MarkdownTextSplitter(chunk_size=MARKDOWN_CHUNK_SIZE, chunk_overlap=MARKDOWN_CHUNK_OVERLAP)
    markdown_docs = markdown_splitter.create_documents([content])
    
    # Further split large sections if needed (using centralized config)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=DEFAULT_CHUNK_SIZE,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP,
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
        
        # Split into smaller chunks if needed (using centralized config)
        if len(doc.page_content) > DEFAULT_CHUNK_SIZE:
            section_chunks = text_splitter.split_text(doc.page_content)
        else:
            section_chunks = [doc.page_content]
            
        for chunk_idx, chunk in enumerate(section_chunks):
            # Use configurable minimum content length
            if len(chunk.strip()) < MIN_CONTENT_LENGTH:
                continue
            
            # Extract chunk-specific keywords including compound phrases (using centralized config)
            chunk_keywords = extract_content_keywords(chunk, max_keywords=MAX_KEYWORDS_PER_CHUNK)
            
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
            })
    
    if filtered_sections > 0:
        print(f"Filtered {filtered_sections} boilerplate sections from {url}")
    
    return chunks

def process_all_content(raw_dir: str = None, processed_dir: str = None) -> Dict:
    """
    Process all markdown files and prepare them for vector storage.
    Uses LLM-based keyword extraction with rule-based fallback.
    
    Args:
        raw_dir (str): Path to directory containing raw markdown files
        processed_dir (str): Path to directory for processed output files
        
    Returns:
        Dict: Processing results and statistics
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_files": 0,
        "total_chunks": 0,
        "filtered_sections": 0,
        "content_types": defaultdict(int),
        "brands": defaultdict(int),
        "files": [],
        "filtering_mode": "LLM-enhanced",
        "min_content_length": MIN_CONTENT_LENGTH,
        "llm_extraction_stats": {
            "successful": 0,
            "fallback": 0,
            "failed": 0
        }
    }
    
    all_chunks = []
    
    print(f"Processing files with {results['filtering_mode']} keyword extraction (min length: {MIN_CONTENT_LENGTH})...")
    print("Note: LLM-based keyword extraction may take longer but provides higher quality keywords.")
    
    # Get list of markdown files
    md_files = [f for f in os.listdir(raw_dir) if f.endswith(".md")]
    total_files = len(md_files)
    
    for idx, filename in enumerate(md_files, 1):
        print(f"Processing file {idx}/{total_files}: {filename[:50]}{'...' if len(filename) > 50 else ''}")
        
        file_path = os.path.join(raw_dir, filename)
        url = filename[:-3].replace("_", "/")
        
        try:
            chunks = process_markdown_file(file_path, url)
            all_chunks.extend(chunks)
            
            # Update statistics
            if chunks:
                first_chunk = chunks[0]
                results["content_types"][first_chunk["content_type"]] += 1
                if first_chunk["brand"]:
                    results["brands"][first_chunk["brand"]] += 1
                
                # Count LLM vs fallback usage (rough estimate)
                if len(first_chunk.get("keywords", [])) > 5:
                    results["llm_extraction_stats"]["successful"] += 1
                else:
                    results["llm_extraction_stats"]["fallback"] += 1
            
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
            results["llm_extraction_stats"]["failed"] += 1
            results["files"].append({
                "filename": filename,
                "url": sanitize_url(url),
                "status": "error",
                "error": str(e)
            })
    
    # Save all chunks to a single file
    chunks_file = os.path.join(processed_dir, "vector_chunks.json")
    print(f"\nSaving {len(all_chunks)} chunks to {chunks_file}")
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Convert defaultdict to regular dict for JSON serialization
    results["content_types"] = dict(results["content_types"])
    results["brands"] = dict(results["brands"])
    
    # Save processing results
    results_file = os.path.join(processed_dir, "processing_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessed {results['total_files']} files into {results['total_chunks']} chunks")
    print(f"LLM extraction stats:")
    print(f"  - Successful: {results['llm_extraction_stats']['successful']}")
    print(f"  - Fallback used: {results['llm_extraction_stats']['fallback']}")
    print(f"  - Failed: {results['llm_extraction_stats']['failed']}")
    
    return results