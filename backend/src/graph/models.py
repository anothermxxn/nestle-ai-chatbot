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

@dataclass
class Relationship:
    """Represents a relationship document in Cosmos DB."""
    id: str
    relationship_type: RelationshipType
    from_entity_id: str
    to_entity_id: str
    properties: Dict[str, Any]
    weight: float = 1.0
    is_user_created: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_cosmos_document(self) -> Dict[str, Any]:
        """
        Convert relationship to Cosmos DB document format.
        
        Returns:
            Dict[str, Any]: Relationship data formatted for Cosmos DB storage
        """
        return {
            "id": self.id,
            "relationship_type": self.relationship_type.value,
            "from_entity_id": self.from_entity_id,
            "to_entity_id": self.to_entity_id,
            "weight": self.weight,
            "is_user_created": self.is_user_created,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            **self.properties
        }
    
    @classmethod
    def from_cosmos_document(cls, doc: Dict[str, Any]) -> "Relationship":
        """
        Create relationship from Cosmos DB document.
        
        Args:
            doc (Dict[str, Any]): Cosmos DB document data
            
        Returns:
            Relationship: Restored relationship object
        """
        properties = {k: v for k, v in doc.items() 
                     if k not in ["id", "relationship_type", "from_entity_id", "to_entity_id", "weight", "is_user_created", "created_at", "updated_at"]}
        
        # Parse timestamps
        created_at = datetime.fromisoformat(doc.get("created_at", datetime.utcnow().isoformat()))
        updated_at = datetime.fromisoformat(doc.get("updated_at", datetime.utcnow().isoformat()))
        
        return cls(
            id=doc["id"],
            relationship_type=RelationshipType(doc["relationship_type"]),
            from_entity_id=doc["from_entity_id"],
            to_entity_id=doc["to_entity_id"],
            properties=properties,
            weight=float(doc.get("weight", 1.0)),
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
        brand (str): Associated brand name
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
    """
    Create a relationship between two entities.
    
    Args:
        from_entity_id (str): Source entity ID
        to_entity_id (str): Target entity ID
        relationship_type (RelationshipType): Type of relationship
        **kwargs: Additional properties for the relationship
        
    Returns:
        Relationship: Relationship object
    """
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
    # Import configuration functions
    from config import detect_topics_from_text
    
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
        
        # Extract topic entities
        content_text = " ".join([
            chunk.get("content", ""),
            chunk.get("page_title", ""),
            chunk.get("section_title", ""),
            " ".join(chunk.get("keywords", []))
        ])
        
        detected_topics = detect_topics_from_text(content_text, min_keyword_matches=1)
        for topic_key, topic_data in detected_topics.items():
            topic_name = topic_data["name"]
            if topic_name not in topic_chunks:
                topic_chunks[topic_name] = []
            topic_chunks[topic_name].append(chunk_id)
        
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