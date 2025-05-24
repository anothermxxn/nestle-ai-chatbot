import logging
from typing import Dict, List, Optional
from datetime import datetime

# Import centralized configurations
try:
    from ...config.content_types import CONTENT_TYPE_KEYWORDS
except ImportError:
    from config.content_types import CONTENT_TYPE_KEYWORDS

logger = logging.getLogger(__name__)

class VectorSearchRanker:
    """
    Relevance ranker that enhances vector search results with additional scoring factors.
    Works with existing vector embeddings and search scores from Azure AI Search.
    """
    
    def __init__(self):
        """Initialize the ranker with scoring weights."""
        self.weights = {
            "vector_score": 1.0,         # Base vector similarity score
            "title_boost": 0.3,          # Additional boost for title matches  
            "content_type_boost": 0.2,   # Boost for content type relevance
            "keyword_boost": 0.2,        # Boost for keyword matches
            "brand_boost": 0.15,         # Boost for brand matches
            "section_boost": 0.1         # Boost for section relevance
        }
    
    def calculate_title_boost(self, query: str, title: str) -> float:
        """
        Calculate additional boost based on title matching.
        
        Args:
            query (str): Search query
            title (str): Document title
            
        Returns:
            float: Title boost factor (0.0 to 1.0)
        """
        if not query or not title:
            return 0.0
            
        query_lower = query.lower()
        title_lower = title.lower()
        
        # Exact match gets highest boost
        if query_lower in title_lower or title_lower in query_lower:
            return 1.0
            
        # Word overlap boost
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        
        if not query_words:
            return 0.0
            
        overlap = len(query_words.intersection(title_words))
        return overlap / len(query_words)
    
    def calculate_content_type_boost(self, query: str, content_type: str) -> float:
        """
        Calculate boost based on content type matching query intent.
        
        Args:
            query (str): Search query
            content_type (str): Document content type
            
        Returns:
            float: Content type boost factor
        """
        if not query or not content_type:
            return 0.0
            
        query_lower = query.lower()
        
        # Check if query suggests a specific content type (using centralized config)
        for content, keywords in CONTENT_TYPE_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                if content_type.lower() == content or content in content_type.lower():
                    return 1.0
                    
        return 0.0
    
    def calculate_keyword_boost(self, query: str, content: str, keywords: List[str]) -> float:
        """
        Calculate boost based on keyword matching in content and metadata.
        
        Args:
            query (str): Search query
            content (str): Document content
            keywords (List[str]): Document keywords
            
        Returns:
            float: Keyword boost factor
        """
        if not query:
            return 0.0
            
        query_lower = query.lower()
        boost = 0.0
        
        # Boost for keywords matching query
        if keywords:
            matching_keywords = sum(1 for kw in keywords if kw.lower() in query_lower)
            if matching_keywords > 0:
                boost += min(matching_keywords * 0.3, 1.0)
        
        # Additional boost for content keyword density
        if content:
            query_words = query_lower.split()
            content_lower = content.lower()
            
            # Count exact phrase matches (higher value)
            if query_lower in content_lower:
                boost += 0.5
            
            # Count individual word matches
            word_matches = sum(1 for word in query_words if word in content_lower)
            if word_matches > 0:
                boost += min(word_matches * 0.1, 0.3)
        
        return min(boost, 1.0)
    
    def calculate_brand_boost(self, query: str, brand: str) -> float:
        """
        Calculate boost based on brand matching.
        
        Args:
            query (str): Search query
            brand (str): Document brand
            
        Returns:
            float: Brand boost factor
        """
        if not query or not brand:
            return 0.0
            
        query_lower = query.lower()
        brand_lower = brand.lower()
        
        # Direct brand mention gets full boost
        if brand_lower in query_lower:
            return 1.0
            
        # Partial brand matching
        brand_words = brand_lower.split()
        query_words = query_lower.split()
        
        matches = sum(1 for brand_word in brand_words if brand_word in query_words)
        if matches > 0:
            return matches / len(brand_words)
            
        return 0.0
    
    def calculate_section_boost(self, query: str, section_title: str) -> float:
        """
        Calculate boost based on section title relevance.
        
        Args:
            query (str): Search query
            section_title (str): Document section title
            
        Returns:
            float: Section boost factor
        """
        if not section_title:
            return 0.0
            
        return self.calculate_title_boost(query, section_title) * 0.7
    
    def extract_vector_score(self, result: Dict) -> float:
        """
        Extract the vector similarity score from Azure Search result.
        
        Args:
            result (Dict): Search result from Azure Search
            
        Returns:
            float: Normalized vector score (0.0 to 1.0)
        """
        # Azure Search returns @search.score for BM25 and vector combination
        search_score = result.get("@search.score", 0.0)
        
        # For hybrid search, the score is already a combination of BM25 and vector
        # Normalize to 0-1 range (typical scores are 0-10+ range)
        normalized_score = min(search_score / 10.0, 1.0) if search_score > 0 else 0.0
        
        return normalized_score
    
    def calculate_enhanced_score(
        self, 
        query: str, 
        result: Dict,
        custom_boosts: Optional[Dict[str, float]] = None
    ) -> Dict:
        """
        Calculate enhanced relevance score combining vector score with custom factors.
        
        Args:
            query (str): Search query
            result (Dict): Search result document
            custom_boosts (Optional[Dict[str, float]]): Custom boost multipliers
            
        Returns:
            Dict: Enhanced result with relevance_score and score_breakdown
        """
        try:
            # Extract base vector score
            vector_score = self.extract_vector_score(result)
            
            # Calculate boost factors
            title_boost = self.calculate_title_boost(
                query, 
                result.get("page_title", "")
            )
            
            content_type_boost = self.calculate_content_type_boost(
                query, 
                result.get("content_type", "")
            )
            
            keyword_boost = self.calculate_keyword_boost(
                query,
                result.get("content", ""),
                result.get("keywords", [])
            )
            
            brand_boost = self.calculate_brand_boost(
                query,
                result.get("brand", "")
            )
            
            section_boost = self.calculate_section_boost(
                query,
                result.get("section_title", "")
            )
            
            # Calculate weighted score
            enhanced_score = (
                vector_score * self.weights["vector_score"] +
                title_boost * self.weights["title_boost"] +
                content_type_boost * self.weights["content_type_boost"] +
                keyword_boost * self.weights["keyword_boost"] +
                brand_boost * self.weights["brand_boost"] +
                section_boost * self.weights["section_boost"]
            )
            
            # Apply custom boosts if provided
            if custom_boosts:
                for boost_field, multiplier in custom_boosts.items():
                    if boost_field in result and result[boost_field]:
                        enhanced_score *= multiplier
            
            # Normalize the final score
            total_possible = sum(self.weights.values())
            normalized_score = enhanced_score / total_possible
            
            # Update result with enhanced scoring
            enhanced_result = result.copy()
            enhanced_result["relevance_score"] = round(min(normalized_score, 1.0), 4)
            enhanced_result["original_vector_score"] = round(vector_score, 4)
            enhanced_result["score_breakdown"] = {
                "vector_similarity": round(vector_score, 3),
                "title_boost": round(title_boost, 3),
                "content_type_boost": round(content_type_boost, 3),
                "keyword_boost": round(keyword_boost, 3),
                "brand_boost": round(brand_boost, 3),
                "section_boost": round(section_boost, 3)
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.warning(f"Error calculating enhanced score: {str(e)}")
            # Return original result with default score
            enhanced_result = result.copy()
            enhanced_result["relevance_score"] = 0.5
            enhanced_result["original_vector_score"] = 0.0
            return enhanced_result
    
    def rank_results(
        self, 
        query: str, 
        results: List[Dict],
        custom_boosts: Optional[Dict[str, float]] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> List[Dict]:
        """
        Rank search results with enhanced scoring.
        
        Args:
            query (str): Search query
            results (List[Dict]): Search results from Azure Search
            custom_boosts (Optional[Dict[str, float]]): Custom boost factors
            custom_weights (Optional[Dict[str, float]]): Custom weight adjustments
            
        Returns:
            List[Dict]: Enhanced and ranked results
        """
        if not results:
            return results
        
        # Temporarily update weights if provided
        original_weights = None
        if custom_weights:
            original_weights = self.weights.copy()
            self.weights.update(custom_weights)
        
        try:
            # Calculate enhanced scores for all results
            enhanced_results = []
            for result in results:
                enhanced_result = self.calculate_enhanced_score(
                    query, 
                    result, 
                    custom_boosts
                )
                enhanced_results.append(enhanced_result)
            
            # Sort by enhanced relevance score (highest first)
            enhanced_results.sort(
                key=lambda x: x["relevance_score"], 
                reverse=True
            )
            
            return enhanced_results
            
        finally:
            # Restore original weights if they were modified
            if original_weights:
                self.weights = original_weights 