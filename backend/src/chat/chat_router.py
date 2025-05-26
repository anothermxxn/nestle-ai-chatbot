import sys
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging

# Setup import paths using centralized helper
from utils.import_helper import setup_imports
setup_imports(__file__)

from chat.chat_client import NestleChatClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/chat", tags=["chat"])

# Global chat client instance
chat_client = None

def get_chat_client():
    """Get or create chat client instance."""
    global chat_client
    if chat_client is None:
        chat_client = NestleChatClient()
    return chat_client

# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat queries."""
    query: str = Field(..., description="User's question or search query", min_length=1)
    content_type: Optional[str] = Field(None, description="Filter by content type (e.g., 'recipe', 'brand')")
    brand: Optional[str] = Field(None, description="Filter by brand (e.g., 'NESTEA')")
    keywords: Optional[List[str]] = Field(None, description="Filter by keywords")
    top_search_results: int = Field(5, description="Number of search results to use", ge=1, le=20)
    use_vector_search: bool = Field(True, description="Whether to use vector search")

class ChatResponse(BaseModel):
    """Response model for chat queries."""
    answer: str = Field(..., description="Generated answer from the AI assistant")
    sources: List[Dict] = Field(..., description="Source documents used for the answer")
    search_results_count: int = Field(..., description="Number of search results used")
    query: str = Field(..., description="Original query")
    filters_applied: Dict = Field(..., description="Filters that were applied")

class RecipeRequest(BaseModel):
    """Request model for recipe suggestions."""
    ingredient: str = Field(..., description="Ingredient to search recipes for", min_length=1)

class ProductRequest(BaseModel):
    """Request model for product information."""
    product_name: str = Field(..., description="Name of the product", min_length=1)

class CookingTipsRequest(BaseModel):
    """Request model for cooking tips."""
    topic: str = Field(..., description="Cooking topic or technique", min_length=1)

class NutritionRequest(BaseModel):
    """Request model for nutrition information."""
    food_item: str = Field(..., description="Food item or product name", min_length=1)

# API Endpoints
@router.post("/search", response_model=ChatResponse)
async def chat_search(request: ChatRequest):
    """
    Perform a conversational search and get an AI-generated answer.
    
    This endpoint combines Azure AI Search with Azure OpenAI to provide
    contextually relevant answers about Nestle products, recipes, and cooking tips.
    
    The RAG (Retrieval-Augmented Generation) pattern is used:
    1. Search for relevant content using Azure AI Search
    2. Format results as sources for the LLM
    3. Generate a grounded response using Azure OpenAI
    """
    try:
        client = get_chat_client()
        
        response = await client.search_and_chat(
            query=request.query,
            content_type=request.content_type,
            brand=request.brand,
            keywords=request.keywords,
            top_search_results=request.top_search_results,
            use_vector_search=request.use_vector_search
        )
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
            
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in chat_search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/recipes", response_model=ChatResponse)
async def get_recipe(request: RecipeRequest):
    """
    Get recipe suggestions for a specific ingredient.
    
    This endpoint focuses on finding recipes that include the specified ingredient,
    returning AI-generated suggestions with cooking instructions and tips.
    """
    try:
        client = get_chat_client()
        response = await client.get_recipe(request.ingredient)
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
            
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in get_recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/products", response_model=ChatResponse)
async def get_product(request: ProductRequest):
    """
    Get information about a specific Nestle product.
    
    This endpoint provides detailed information about Nestle products,
    including descriptions, uses, and related recipes.
    """
    try:
        client = get_chat_client()
        response = await client.get_product(request.product_name)
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
            
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in get_product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/cooking-tips", response_model=ChatResponse)
async def get_cooking_tips(request: CookingTipsRequest):
    """
    Get cooking tips and advice for a specific topic.
    
    This endpoint provides cooking tips, techniques, and advice
    related to baking, preparation, and culinary techniques.
    """
    try:
        client = get_chat_client()
        response = await client.get_cooking_tips(request.topic)
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
            
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in get_cooking_tips: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/nutrition", response_model=ChatResponse)
async def get_nutrition_info(request: NutritionRequest):
    """
    Get nutritional information about a food item or Nestle product.
    
    This endpoint provides nutritional facts, calorie information,
    and health benefits for various food items and products.
    """
    try:
        client = get_chat_client()
        response = await client.ask_about_nutrition(request.food_item)
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
            
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Error in get_nutrition_info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/quick-search")
async def quick_search(
    q: str = Query(..., description="Quick search query", min_length=1),
    type: Optional[str] = Query(None, description="Content type filter"),
    brand: Optional[str] = Query(None, description="Brand filter"),
    limit: int = Query(5, description="Number of results", ge=1, le=20)
):
    """
    Quick search endpoint for simple queries.
    
    This is a simplified endpoint for quick searches without the full request body.
    Useful for testing and simple integrations.
    """
    try:
        client = get_chat_client()
        
        response = await client.search_and_chat(
            query=q,
            content_type=type,
            brand=brand,
            top_search_results=limit
        )
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])
            
        return response
        
    except Exception as e:
        logger.error(f"Error in quick_search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the chat service.
    
    Returns the status of the chat client and its dependencies.
    This endpoint performs a lightweight test to verify all components are working.
    """
    try:
        client = get_chat_client()
        
        # Test a simple query to verify everything is working
        test_response = await client.search_and_chat(
            query="test",
            top_search_results=1
        )
        
        return {
            "status": "healthy",
            "chat_client": "operational",
            "search_client": "operational",
            "test_query_successful": "error" not in test_response,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/examples")
async def get_example_queries():
    """
    Get example queries for testing the chat functionality.
    
    Returns a list of sample queries that can be used to test
    different aspects of the chat system.
    """
    return {
        "general_queries": [
            "What is KitKat?",
            "How do I make chocolate chip cookies?",
            "Tell me about Nescafe products"
        ],
        "recipe_queries": [
            "Show me chocolate dessert recipes",
            "How to bake cookies with vanilla",
            "Coffee-flavored desserts"
        ],
        "product_queries": [
            "Information about Quality Street",
            "Smarties candy details",
            "Nescafe instant coffee varieties"
        ],
        "cooking_tips": [
            "Tips for melting chocolate",
            "How to brew better coffee",
            "Cookie baking techniques"
        ],
        "nutrition_queries": [
            "Nutrition facts for dark chocolate",
            "Calories in KitKat",
            "Health benefits of coffee"
        ]
    } 