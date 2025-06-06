import logging
from typing import Dict
import json
import os

try:
    from backend.config.brands import BRAND_CATEGORIES
    from backend.src.graph.models.entity import EntityType
    from backend.src.graph.services.cosmos_service import CosmosGraphClient
except ImportError:
    from config.brands import BRAND_CATEGORIES
    from src.graph.models.entity import EntityType
    from src.graph.services.cosmos_service import CosmosGraphClient

logger = logging.getLogger(__name__)

class CountStatisticsService:
    """
    Service for providing count statistics from the graph database.
    
    Provides functionality for:
    - Entity counts by type
    - Product counts by category
    - Product counts by brand
    - Recipe counts
    """
    
    def __init__(self):
        """Initialize the count statistics service."""
        try:
            self.cosmos_client = CosmosGraphClient()
            logger.info("Successfully initialized CountStatisticsService")
        except Exception as e:
            logger.error(f"Failed to initialize CountStatisticsService: {str(e)}")
            raise
    
    async def get_entity_counts(self) -> Dict[str, int]:
        """
        Query entity counts by type from graph database.
        
        Returns:
            Dict[str, int]: Dictionary mapping entity types to their counts
        """
        try:
            entity_counts = {}
            
            # Count each entity type
            for entity_type in EntityType:
                try:
                    entities = await self.cosmos_client.find_entities_by_type(
                        entity_type=entity_type,
                        limit=10000 
                    )
                    entity_counts[entity_type.value.lower()] = len(entities)
                    logger.debug(f"Found {len(entities)} entities of type {entity_type.value}")
                except Exception as e:
                    logger.error(f"Failed to count entities of type {entity_type.value}: {str(e)}")
                    entity_counts[entity_type.value.lower()] = 0
            
            logger.info(f"Entity counts retrieved: {entity_counts}")
            return entity_counts
            
        except Exception as e:
            logger.error(f"Failed to get entity counts: {str(e)}")
            return {}
    
    async def get_product_counts_by_category(self) -> Dict[str, int]:
        """
        Implement product counts by category using brand categories from existing brand config.
        
        Returns:
            Dict[str, int]: Dictionary mapping categories to product counts
        """
        try:
            category_counts = {}
            
            # Get all product entities
            products = await self.cosmos_client.find_entities_by_type(
                entity_type=EntityType.PRODUCT,
                limit=10000
            )
            
            # Count products by category using brand information
            for product in products:
                product_brand = product.properties.get("brand", "")
                if product_brand:
                    # Find category for this brand
                    category = None
                    for cat, brands in BRAND_CATEGORIES.items():
                        if product_brand in brands:
                            category = cat
                            break
                    
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1
                    else:
                        # If no category found, add to "other"
                        category_counts["other"] = category_counts.get("other", 0) + 1
                else:
                    # Products without brand go to "other"
                    category_counts["other"] = category_counts.get("other", 0) + 1
            
            logger.info(f"Product counts by category: {category_counts}")
            return category_counts
            
        except Exception as e:
            logger.error(f"Failed to get product counts by category: {str(e)}")
            return {}
    
    async def get_product_counts_by_brand(self) -> Dict[str, int]:
        """
        Implement brand-specific product counting.
        
        Returns:
            Dict[str, int]: Dictionary mapping brand names to product counts
        """
        try:
            brand_counts = {}
            
            # Get all product entities
            products = await self.cosmos_client.find_entities_by_type(
                entity_type=EntityType.PRODUCT,
                limit=10000
            )
            
            # Count products by brand
            for product in products:
                product_brand = product.properties.get("brand", "")
                if product_brand:
                    brand_counts[product_brand] = brand_counts.get(product_brand, 0) + 1
                else:
                    # Products without brand
                    brand_counts["unknown"] = brand_counts.get("unknown", 0) + 1
            
            logger.info(f"Product counts by brand: {brand_counts}")
            return brand_counts
            
        except Exception as e:
            logger.error(f"Failed to get product counts by brand: {str(e)}")
            return {}
    
    async def get_recipe_counts(self) -> Dict[str, int]:
        """
        Implement recipe statistics counting.
        
        Returns:
            Dict[str, int]: Dictionary with recipe statistics
        """
        try:
            recipe_stats = {}
            
            # Get all recipe entities
            recipes = await self.cosmos_client.find_entities_by_type(
                entity_type=EntityType.RECIPE,
                limit=10000
            )
            
            # Total recipe count
            recipe_stats["total"] = len(recipes)
            
            # Count recipes by type if available
            recipe_type_counts = {}
            for recipe in recipes:
                recipe_type = recipe.properties.get("recipe_type", "")
                if recipe_type:
                    recipe_type_counts[recipe_type] = recipe_type_counts.get(recipe_type, 0) + 1
                else:
                    recipe_type_counts["unknown"] = recipe_type_counts.get("unknown", 0) + 1
            
            recipe_stats["by_type"] = recipe_type_counts
            
            logger.info(f"Recipe counts: {recipe_stats}")
            return recipe_stats
            
        except Exception as e:
            logger.error(f"Failed to get recipe counts: {str(e)}")
            return {"total": 0, "by_type": {}} 