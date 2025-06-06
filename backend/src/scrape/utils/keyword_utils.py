import re

try:
    from backend.config import STOP_WORDS
except ImportError:
    from config import STOP_WORDS

def is_meaningful_keyword(word: str) -> bool:
    """
    Check if a keyword is meaningful for search purposes.
    Filters out only technical web terms and artifacts that LLMs might miss.
    
    Args:
        word (str): Word to check
        
    Returns:
        bool: True if word is meaningful as a keyword
    """
    word_lower = word.lower()
    
    # Skip if it's in stop words
    if word_lower in STOP_WORDS:
        return False
    
    # Skip pure numbers or number-heavy strings
    if word.isdigit() or len(re.findall(r'\d', word)) > len(word) // 2:
        return False
    
    # Skip very short terms
    if len(word) <= 2 and word_lower not in {'qt', 'ml', 'oz', 'lb', 'kg', 'mg'}:
        return False
    
    # Skip URL fragments and malformed terms
    if any(fragment in word_lower for fragment in ['https', 'http', 'www.', '.com', '.ca', '.org']):
        return False
    
    return True 