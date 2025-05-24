from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass
import uuid

class EntityType(Enum):
    """Enumeration of all supported entity types."""
    BRAND = "Brand"
    TOPIC = "Topic"
    PRODUCT = "Product"
    RECIPE = "Recipe"

class RelationshipType(Enum):
    """Enumeration of all supported relationship types."""
    BELONGS_TO = "BELONGS_TO"      # Product -> Brand
    MENTIONS = "MENTIONS"          # Topic/Product -> Brand
    CONTAINS = "CONTAINS"          # Recipe -> Product
    RELATED_TO = "RELATED_TO"      # Generic relationships
    FEATURED_IN = "FEATURED_IN"    # Brand/Product -> Topic

@dataclass
class Entity:
    """Represents an entity document in Cosmos DB."""
    id: str
    entity_type: EntityType
    properties: Dict[str, Any]
    
    def to_cosmos_document(self) -> Dict[str, Any]:
        """Convert entity to Cosmos DB document format."""
        doc = {
            "id": self.id,
            "entity_type": self.entity_type.value,
            **self.properties
        }
        return doc
    
    @classmethod
    def from_cosmos_document(cls, doc: Dict[str, Any]) -> "Entity":
        """Create entity from Cosmos DB document."""
        properties = {k: v for k, v in doc.items() 
                     if k not in ["id", "entity_type"]}
        
        return cls(
            id=doc["id"],
            entity_type=EntityType(doc["entity_type"]),
            properties=properties
        )

@dataclass
class Relationship:
    """Represents a relationship document in Cosmos DB."""
    id: str
    relationship_type: RelationshipType
    from_entity_id: str
    to_entity_id: str
    properties: Dict[str, Any]
    weight: float = 1.0
    
    def to_cosmos_document(self) -> Dict[str, Any]:
        """Convert relationship to Cosmos DB document format."""
        return {
            "id": self.id,
            "relationship_type": self.relationship_type.value,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "weight": self.weight,
            **self.properties
        }
    
    @classmethod
    def from_cosmos_document(cls, doc: Dict[str, Any]) -> "Relationship":
        """Create relationship from Cosmos DB document."""
        properties = {k: v for k, v in doc.items() 
                     if k not in ["id", "relationship_type", "from_entity_id", "to_entity_id", "weight"]}
        
        return cls(
            id=doc["id"],
            relationship_type=RelationshipType(doc["relationship_type"]),
            from_entity_id=doc["from_entity_id"],
            to_entity_id=doc["to_entity_id"],
            properties=properties,
            weight=float(doc.get("weight", 1.0))
        )

def create_brand_entity(name: str, chunk_ids: List[str] = None, **kwargs) -> Entity:
    """Create a Brand entity with proper categorization."""
    from .config import normalize_brand_name, get_brand_category
    
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
    """Create a Topic entity."""
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
    """Create a Product entity."""
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
    """Create a Recipe entity."""
    properties = {
        "title": title,
        "recipe_type": kwargs.get("recipe_type", "general"),
        "keywords": kwargs.get("keywords", []),
        "ingredients_mentioned": kwargs.get("ingredients_mentioned", []),
        "chunk_count": len(chunk_ids) if chunk_ids else 0,
        "chunk_ids": chunk_ids or []
    }
    return Entity(
        id=f"recipe_{title.lower().replace(' ', '_')[:50]}",
        entity_type=EntityType.RECIPE,
        properties=properties
    )

def create_relationship(from_entity_id: str, to_entity_id: str, 
                       relationship_type: RelationshipType, **kwargs) -> Relationship:
    """Create a relationship between two entities."""
    return Relationship(
        id=f"rel_{uuid.uuid4().hex[:8]}",
        relationship_type=relationship_type,
        from_entity_id=from_entity_id,
        to_entity_id=to_entity_id,
        properties=kwargs
    )

def extract_entities_from_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, List[Entity]]:
    """
    Extract higher-level entities from a collection of content chunks.
    
    Args:
        chunks (List[Dict[str, Any]]): List of content chunk data
        
    Returns:
        Dict[str, List[Entity]]: Dictionary of entity types and their instances
    """
    from .config import extract_topics_from_keywords
    
    entities = {
        "brands": {},
        "topics": {},
        "products": {},
        "recipes": {}
    }
    
    # Group chunks by entities
    brand_chunks = {}
    topic_chunks = {}
    recipe_chunks = {}
    
    for chunk in chunks:
        chunk_id = chunk.get("id")
        
        # Extract brand entities
        if chunk.get("brand"):
            brand_name = chunk["brand"]
            if brand_name not in brand_chunks:
                brand_chunks[brand_name] = []
            brand_chunks[brand_name].append(chunk_id)
        
        # Extract topic entities from keywords
        keywords = chunk.get("keywords", [])
        topics = extract_topics_from_keywords(keywords)
        for topic in topics:
            if topic not in topic_chunks:
                topic_chunks[topic] = []
            topic_chunks[topic].append(chunk_id)
        
        # Extract recipe entities
        if chunk.get("content_type") == "recipe":
            recipe_title = chunk.get("page_title", "Unknown Recipe")
            if recipe_title not in recipe_chunks:
                recipe_chunks[recipe_title] = []
            recipe_chunks[recipe_title].append(chunk_id)
    
    # Create brand entities
    for brand_name, chunk_ids in brand_chunks.items():
        brand_entity = create_brand_entity(
            name=brand_name,
            chunk_ids=chunk_ids,
            content_types=list(set(chunk.get("content_type") for chunk in chunks if chunk.get("brand") == brand_name))
        )
        entities["brands"][brand_name] = brand_entity
    
    # Create topic entities
    for topic_name, chunk_ids in topic_chunks.items():
        topic_entity = create_topic_entity(
            name=topic_name,
            category="content_theme",
            chunk_ids=chunk_ids
        )
        entities["topics"][topic_name] = topic_entity
    
    # Create recipe entities
    for recipe_title, chunk_ids in recipe_chunks.items():
        recipe_entity = create_recipe_entity(
            title=recipe_title,
            chunk_ids=chunk_ids
        )
        entities["recipes"][recipe_title] = recipe_entity
    
    return entities

def create_entity_relationships(entities: Dict[str, Dict[str, Entity]]) -> List[Relationship]:
    """
    Create relationships between extracted entities.
    
    Args:
        entities (Dict[str, Dict[str, Entity]]): Dictionary of extracted entities
        
    Returns:
        List[Relationship]: List of relationships between entities
    """
    relationships = []
    
    brands = entities.get("brands", {})
    topics = entities.get("topics", {})
    recipes = entities.get("recipes", {})
    
    # Create Brand -> Topic relationships (brands featured in topics)
    for brand_name, brand_entity in brands.items():
        for topic_name, topic_entity in topics.items():
            # Check if brand and topic share any chunk IDs
            brand_chunks = set(brand_entity.properties.get("chunk_ids", []))
            topic_chunks = set(topic_entity.properties.get("chunk_ids", []))
            
            shared_chunks = brand_chunks.intersection(topic_chunks)
            if shared_chunks:
                rel = create_relationship(
                    brand_entity.id,
                    topic_entity.id,
                    RelationshipType.FEATURED_IN,
                    shared_chunks=list(shared_chunks),
                    confidence=len(shared_chunks) / len(brand_chunks) if brand_chunks else 0
                )
                relationships.append(rel)
    
    # Create Recipe -> Brand relationships (recipes mention brands)
    for recipe_name, recipe_entity in recipes.items():
        for brand_name, brand_entity in brands.items():
            # Check if recipe and brand share any chunk IDs
            recipe_chunks = set(recipe_entity.properties.get("chunk_ids", []))
            brand_chunks = set(brand_entity.properties.get("chunk_ids", []))
            
            shared_chunks = recipe_chunks.intersection(brand_chunks)
            if shared_chunks:
                rel = create_relationship(
                    recipe_entity.id,
                    brand_entity.id,
                    RelationshipType.MENTIONS,
                    shared_chunks=list(shared_chunks),
                    confidence=len(shared_chunks) / len(recipe_chunks) if recipe_chunks else 0
                )
                relationships.append(rel)
    
    return relationships

def find_entity_by_chunk_id(entities: Dict[str, Dict[str, Entity]], chunk_id: str) -> List[Entity]:
    """
    Find all entities that reference a specific chunk ID.
    
    Args:
        entities (Dict[str, Dict[str, Entity]]): Dictionary of extracted entities  
        chunk_id (str): The chunk ID to search for
        
    Returns:
        List[Entity]: List of entities that reference the chunk
    """
    related_entities = []
    
    for entity_type, entity_dict in entities.items():
        for entity_name, entity in entity_dict.items():
            chunk_ids = entity.properties.get("chunk_ids", [])
            if chunk_id in chunk_ids:
                related_entities.append(entity)
    
    return related_entities 