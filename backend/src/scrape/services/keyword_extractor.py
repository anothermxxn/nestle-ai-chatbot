import asyncio
import logging
import json
import re
from typing import List, Optional
from openai import AsyncAzureOpenAI, AzureOpenAI

# Dynamic import to handle both local development and Docker environments
try:
    from backend.config.azure_ai import AZURE_OPENAI_CONFIG, validate_azure_openai_config
except ImportError:
    from config.azure_ai import AZURE_OPENAI_CONFIG, validate_azure_openai_config
from ..utils.keyword_utils import is_meaningful_keyword

class LLMKeywordExtractor:
    """LLM-based keyword extractor using Azure OpenAI"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Azure OpenAI client"""
        if not validate_azure_openai_config():
            print("Warning: Azure OpenAI configuration invalid. LLM keyword extraction will be disabled.")
            return
        
        try:
            self.client = AsyncAzureOpenAI(
                api_key=AZURE_OPENAI_CONFIG["api_key"],
                api_version=AZURE_OPENAI_CONFIG["api_version"],
                azure_endpoint=AZURE_OPENAI_CONFIG["endpoint"]
            )
            print("LLM keyword extractor initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None
    
    def _create_keyword_prompt(self, content: str, title: str, content_type: str, brand: Optional[str] = None) -> str:
        """Create a prompt for keyword extraction"""
        
        # Truncate content if too long to fit in context window
        max_content_length = 2000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        prompt = f"""Extract 5-10 meaningful keywords for search and categorization from this {content_type} content about food, recipes, or nutrition products.

        Title: {title}
        Brand: {brand or 'Not specified'}
        Content Type: {content_type}
        Content: {content}

        FOCUS ON extracting keywords that are:
        - Food ingredients (chocolate, vanilla, strawberry, etc.)
        - Cooking methods (baking, grilling, mixing, etc.)
        - Product names and brands
        - Nutritional terms (protein, vitamins, calories, etc.)
        - Meal types and occasions (breakfast, dessert, snack, etc.)
        - Recipe-related terms (prep time, ingredients, etc.)
        - Food descriptors (creamy, crispy, sweet, etc.)

        EXCLUDE:
        - Social media terms (facebook, twitter, instagram, email, etc.)
        - Web/technical terms (cookies, tracking, analytics, etc.)
        - Generic adjectives (good, great, best, new, etc.)
        - Navigation terms (next, previous, more, etc.)
        - URL fragments or web addresses
        - Common stop words (the, and, of, etc.)

        Return ONLY a JSON object with a "keywords" array, like: {{"keywords": ["keyword1", "keyword2", "keyword3"]}}"""

        return prompt
    
    async def extract_keywords_async(self, content: str, title: str, content_type: str, brand: Optional[str] = None) -> List[str]:
        """Extract keywords using LLM asynchronously"""
        try:
            prompt = self._create_keyword_prompt(content, title, content_type, brand)
            
            response = await self.client.chat.completions.create(
                model=AZURE_OPENAI_CONFIG["deployment"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response more robustly
            keywords = []
            try:
                # Try to parse as JSON object first
                json_data = json.loads(response_text)
                
                # Extract keywords from different possible structures
                if isinstance(json_data, dict):
                    if "keywords" in json_data:
                        keywords = json_data["keywords"]
                    elif "items" in json_data:
                        keywords = json_data["items"]
                    else:
                        # Try to get values from the first key
                        first_key = next(iter(json_data.keys()))
                        potential_keywords = json_data[first_key]
                        if isinstance(potential_keywords, list):
                            keywords = potential_keywords
                        else:
                            keywords = list(json_data.values())[0] if json_data.values() else []
                elif isinstance(json_data, list):
                    keywords = json_data
                else:
                    keywords = []
                    
            except json.JSONDecodeError as json_err:
                print(f"JSON decode error: {json_err}")
                print(f"Response text: {response_text}")
                
                # Fallback: try to extract keywords using regex
                keyword_patterns = [
                    r'"([^"]+)"',  # Quoted strings
                    r'[\w\s]+',    # Word sequences
                ]
                
                for pattern in keyword_patterns:
                    matches = re.findall(pattern, response_text)
                    if matches:
                        keywords = [m.strip() for m in matches if len(m.strip()) > 2]
                        break
                
                if not keywords:
                    # Final fallback: split by common separators
                    keywords = [k.strip() for k in re.split(r'[,\n\r]', response_text) if k.strip()]
            
            # Clean and validate keywords
            cleaned_keywords = []
            for keyword in keywords:
                if isinstance(keyword, str):
                    keyword = keyword.strip().lower()
                    # Remove quotes and extra whitespace
                    keyword = keyword.strip('"\'')
                    if len(keyword) > 2 and is_meaningful_keyword(keyword):
                        cleaned_keywords.append(keyword)
            
            # Always include content type and brand
            result_keywords = [content_type]
            if brand and brand.lower() != content_type:
                result_keywords.append(brand.lower())
            
            # Add LLM-extracted keywords
            result_keywords.extend(cleaned_keywords[:8])  # Limit to 8 LLM keywords
            
            return list(set(result_keywords))  # Remove duplicates
            
        except Exception as e:
            print(f"LLM keyword extraction failed: {e}")
            return []
    
    def extract_keywords_sync(self, content: str, title: str, content_type: str, brand: Optional[str] = None) -> List[str]:
        """Extract keywords synchronously (wrapper for async method)"""
        try:
            # Create new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(
                self.extract_keywords_async(content, title, content_type, brand)
            )
        except Exception as e:
            print(f"Sync keyword extraction failed: {e}")
            return []

def extract_keywords_with_llm(content: str, title: str, content_type: str, brand: Optional[str] = None) -> List[str]:
    """Extract keywords using LLM - main entry point"""
    extractor = LLMKeywordExtractor()
    return extractor.extract_keywords_sync(content, title, content_type, brand)