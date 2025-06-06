from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class EntityType(Enum):
    """Enumeration of all supported entity types."""
    BRAND = "Brand"
    TOPIC = "Topic"
    PRODUCT = "Product"
    RECIPE = "Recipe"

@dataclass
class Entity:
    """Represents an entity document in Cosmos DB."""
    id: str
    entity_type: EntityType
    properties: Dict[str, Any]
    is_user_created: bool = False  # Flag to distinguish user-created vs system-created entities
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_cosmos_document(self) -> Dict[str, Any]:
        """
        Convert entity to Cosmos DB document format.
        
        Returns:
            Dict[str, Any]: Entity data formatted for Cosmos DB storage
        """
        doc = {
            "id": self.id,
            "entity_type": self.entity_type.value,
            "is_user_created": self.is_user_created,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            **self.properties
        }
        return doc
    
    @classmethod
    def from_cosmos_document(cls, doc: Dict[str, Any]) -> "Entity":
        """
        Create entity from Cosmos DB document.
        
        Args:
            doc (Dict[str, Any]): Cosmos DB document data
            
        Returns:
            Entity: Restored entity object
        """
        properties = {k: v for k, v in doc.items() 
                     if k not in ["id", "entity_type", "is_user_created", "created_at", "updated_at"]}
        
        # Parse timestamps
        created_at = datetime.fromisoformat(doc.get("created_at", datetime.utcnow().isoformat()))
        updated_at = datetime.fromisoformat(doc.get("updated_at", datetime.utcnow().isoformat()))
        
        return cls(
            id=doc["id"],
            entity_type=EntityType(doc["entity_type"]),
            properties=properties,
            is_user_created=doc.get("is_user_created", False),
            created_at=created_at,
            updated_at=updated_at
        )

def create_brand_entity(name: str, chunk_ids: List[str] = None, **kwargs) -> Entity:
    """
    Create a Brand entity with proper categorization.
    
    Args:
        name (str): Brand name
        chunk_ids (List[str]): List of chunk IDs associated with this brand
        **kwargs: Additional properties for the brand
        
    Returns:
        Entity: Brand entity object
    """
    # Import configuration functions
    from config import normalize_brand_name, get_brand_category
    
    normalized_name = normalize_brand_name(name)
    if not normalized_name:
        normalized_name = name
    
    category = get_brand_category(normalized_name)
    
    properties = {
        "name": normalized_name,
        "description": kwargs.get("description", ""),
        "category": category,
        "content_types": kwargs.get("content_types", []),
        "chunk_count": len(chunk_ids) if chunk_ids else 0,
        "chunk_ids": chunk_ids or []
    }
    return Entity(
        id=f"brand_{normalized_name.lower().replace(' ', '_').replace('-', '_')}",
        entity_type=EntityType.BRAND,
        properties=properties
    )

def create_topic_entity(name: str, category: str, chunk_ids: List[str] = None, **kwargs) -> Entity:
    """
    Create a Topic entity.
    
    Args:
        name (str): Topic name
        category (str): Topic category
        chunk_ids (List[str]): List of chunk IDs associated with this topic
        **kwargs: Additional properties for the topic
        
    Returns:
        Entity: Topic entity object
    """
    properties = {
        "name": name,
        "category": category,
        "description": kwargs.get("description", ""),
        "keywords": kwargs.get("keywords", []),
        "chunk_count": len(chunk_ids) if chunk_ids else 0,
        "chunk_ids": chunk_ids or []
    }
    return Entity(
        id=f"topic_{name.lower().replace(' ', '_')}",
        entity_type=EntityType.TOPIC,
        properties=properties
    )

def create_product_entity(name: str, brand: str = "", chunk_ids: List[str] = None, **kwargs) -> Entity:
    """
    Create a Product entity.
    
    Args:
        name (str): Product name
        brand (str): Brand name (optional)
        chunk_ids (List[str]): List of chunk IDs associated with this product
        **kwargs: Additional properties for the product
        
    Returns:
        Entity: Product entity object
    """
    properties = {
        "name": name,
        "brand": brand,
        "category": kwargs.get("category", ""),
        "description": kwargs.get("description", ""),
        "chunk_count": len(chunk_ids) if chunk_ids else 0,
        "chunk_ids": chunk_ids or []
    }
    return Entity(
        id=f"product_{name.lower().replace(' ', '_')}",
        entity_type=EntityType.PRODUCT,
        properties=properties
    )

def create_recipe_entity(title: str, chunk_ids: List[str] = None, **kwargs) -> Entity:
    """
    Create a Recipe entity.
    
    Args:
        title (str): Recipe title
        chunk_ids (List[str]): List of chunk IDs associated with this recipe
        **kwargs: Additional properties for the recipe
        
    Returns:
        Entity: Recipe entity object
    """
    properties = {
        "title": title,
        "recipe_type": kwargs.get("recipe_type", ""),
        "keywords": kwargs.get("keywords", []),
        "ingredients_mentioned": kwargs.get("ingredients_mentioned", []),
        "chunk_count": len(chunk_ids) if chunk_ids else 0,
        "chunk_ids": chunk_ids or []
    }
    return Entity(
        id=f"recipe_{title.lower().replace(' ', '_')}",
        entity_type=EntityType.RECIPE,
        properties=properties
    )

def extract_entities_from_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, List[Entity]]:
    """
    Extract entities from processed chunks.
    
    Args:
        chunks (List[Dict[str, Any]]): List of processed chunks
        
    Returns:
        Dict[str, List[Entity]]: Dictionary mapping entity types to lists of entities
    """
    entities = {
        "brands": [],
        "topics": [],
        "products": [],
        "recipes": []
    }
    
    # Track unique entities to avoid duplicates
    seen_brands = set()
    seen_topics = set()
    seen_products = set()
    seen_recipes = set()
    
    for chunk in chunks:
        chunk_id = chunk.get("id", "")
        content_type = chunk.get("content_type", "")
        brand = chunk.get("brand", "")
        keywords = chunk.get("keywords", [])
        page_title = chunk.get("page_title", "")
        
        # Extract brand entities
        if brand and brand not in seen_brands:
            brand_entity = create_brand_entity(
                name=brand,
                chunk_ids=[chunk_id],
                content_types=[content_type]
            )
            entities["brands"].append(brand_entity)
            seen_brands.add(brand)
        elif brand and brand in seen_brands:
            # Update existing brand entity with new chunk
            for brand_entity in entities["brands"]:
                if brand_entity.properties["name"] == brand:
                    brand_entity.properties["chunk_ids"].append(chunk_id)
                    brand_entity.properties["chunk_count"] += 1
                    if content_type not in brand_entity.properties["content_types"]:
                        brand_entity.properties["content_types"].append(content_type)
                    break
        
        # Extract topic entities from keywords
        for keyword in keywords:
            if keyword not in seen_topics and len(keyword) > 2:
                topic_entity = create_topic_entity(
                    name=keyword,
                    category="keyword",
                    chunk_ids=[chunk_id]
                )
                entities["topics"].append(topic_entity)
                seen_topics.add(keyword)
            elif keyword in seen_topics:
                # Update existing topic entity
                for topic_entity in entities["topics"]:
                    if topic_entity.properties["name"] == keyword:
                        topic_entity.properties["chunk_ids"].append(chunk_id)
                        topic_entity.properties["chunk_count"] += 1
                        break
        
        # Extract product entities (from page titles that look like products)
        if content_type == "product" and page_title and page_title not in seen_products:
            product_entity = create_product_entity(
                name=page_title,
                brand=brand,
                chunk_ids=[chunk_id]
            )
            entities["products"].append(product_entity)
            seen_products.add(page_title)
        elif content_type == "product" and page_title in seen_products:
            # Update existing product entity
            for product_entity in entities["products"]:
                if product_entity.properties["name"] == page_title:
                    product_entity.properties["chunk_ids"].append(chunk_id)
                    product_entity.properties["chunk_count"] += 1
                    break
        
        # Extract recipe entities
        if content_type == "recipe" and page_title and page_title not in seen_recipes:
            recipe_entity = create_recipe_entity(
                title=page_title,
                chunk_ids=[chunk_id],
                keywords=keywords
            )
            entities["recipes"].append(recipe_entity)
            seen_recipes.add(page_title)
        elif content_type == "recipe" and page_title in seen_recipes:
            # Update existing recipe entity
            for recipe_entity in entities["recipes"]:
                if recipe_entity.properties["title"] == page_title:
                    recipe_entity.properties["chunk_ids"].append(chunk_id)
                    recipe_entity.properties["chunk_count"] += 1
                    # Merge keywords
                    existing_keywords = set(recipe_entity.properties.get("keywords", []))
                    new_keywords = set(keywords)
                    recipe_entity.properties["keywords"] = list(existing_keywords | new_keywords)
                    break
    
    return entities

def find_entity_by_chunk_id(entities: Dict[str, Dict[str, Entity]], chunk_id: str) -> List[Entity]:
    """
    Find all entities that reference a specific chunk ID.
    
    Args:
        entities (Dict[str, Dict[str, Entity]]): Dictionary of entities organized by type and ID
        chunk_id (str): Chunk ID to search for
        
    Returns:
        List[Entity]: List of entities that reference the chunk ID
    """
    matching_entities = []
    
    for entity_type, entity_dict in entities.items():
        for entity_id, entity in entity_dict.items():
            chunk_ids = entity.properties.get("chunk_ids", [])
            if chunk_id in chunk_ids:
                matching_entities.append(entity)
    
    return matching_entities 