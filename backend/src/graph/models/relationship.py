from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class RelationshipType(Enum):
    """Enumeration of all supported relationship types."""
    BELONGS_TO = "BELONGS_TO"      # Product -> Brand
    MENTIONS = "MENTIONS"          # Topic/Product -> Brand
    CONTAINS = "CONTAINS"          # Recipe -> Product
    RELATED_TO = "RELATED_TO"      # Generic relationships
    FEATURED_IN = "FEATURED_IN"    # Brand/Product -> Topic

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

def create_entity_relationships(entities: Dict[str, Dict[str, Any]]) -> List[Relationship]:
    """
    Create relationships between extracted entities.
    
    Args:
        entities (Dict[str, Dict[str, Any]]): Dictionary of extracted entities
        
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