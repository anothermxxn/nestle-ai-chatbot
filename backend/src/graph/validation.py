from typing import Dict, Any, List, Optional

try:
    from backend.src.graph.models import EntityType, RelationshipType
except ImportError:
    from src.graph.models import EntityType, RelationshipType

# Required properties for each entity type
ENTITY_REQUIRED_PROPERTIES = {
    EntityType.BRAND: {"name"},
    EntityType.TOPIC: {"name", "category"},
    EntityType.PRODUCT: {"name"},
    EntityType.RECIPE: {"title"}
}

# Optional properties for each entity type (system-created entities)
ENTITY_OPTIONAL_PROPERTIES = {
    EntityType.BRAND: {"description", "category", "content_types", "chunk_count", "chunk_ids"},
    EntityType.TOPIC: {"description", "keywords", "chunk_count", "chunk_ids"},
    EntityType.PRODUCT: {"brand", "category", "description", "chunk_count", "chunk_ids"},
    EntityType.RECIPE: {"recipe_type", "keywords", "ingredients_mentioned", "chunk_count", "chunk_ids"}
}

# Optional properties for user-created entities (no chunk-related properties)
USER_ENTITY_OPTIONAL_PROPERTIES = {
    EntityType.BRAND: {"description", "category", "content_types"},
    EntityType.TOPIC: {"description", "keywords"},
    EntityType.PRODUCT: {"brand", "category", "description"},
    EntityType.RECIPE: {"recipe_type", "keywords", "ingredients_mentioned"}
}

# Valid relationship combinations (from_type -> to_type -> allowed_relationships)
VALID_RELATIONSHIP_COMBINATIONS = {
    EntityType.PRODUCT: {
        EntityType.BRAND: {RelationshipType.BELONGS_TO},
        EntityType.TOPIC: {RelationshipType.FEATURED_IN},
        EntityType.RECIPE: {RelationshipType.RELATED_TO}
    },
    EntityType.BRAND: {
        EntityType.TOPIC: {RelationshipType.FEATURED_IN},
        EntityType.BRAND: {RelationshipType.RELATED_TO}
    },
    EntityType.TOPIC: {
        EntityType.BRAND: {RelationshipType.MENTIONS},
        EntityType.PRODUCT: {RelationshipType.MENTIONS},
        EntityType.TOPIC: {RelationshipType.RELATED_TO}
    },
    EntityType.RECIPE: {
        EntityType.PRODUCT: {RelationshipType.CONTAINS},
        EntityType.BRAND: {RelationshipType.MENTIONS},
        EntityType.RECIPE: {RelationshipType.RELATED_TO}
    }
}

def is_valid_entity_type(entity_type: str) -> bool:
    """
    Check if an entity type is valid (one of the 4 pre-defined types).
    
    Args:
        entity_type: Entity type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        EntityType(entity_type)
        return True
    except ValueError:
        return False

def is_valid_relationship_type(relationship_type: str) -> bool:
    """
    Check if a relationship type is valid (one of the pre-defined types).
    
    Args:
        relationship_type: Relationship type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        RelationshipType(relationship_type)
        return True
    except ValueError:
        return False

def validate_entity_properties(entity_type: str, properties: Dict[str, Any], is_user_created: bool = False) -> List[str]:
    """
    Validate entity properties against requirements.
    
    Args:
        entity_type: Entity type
        properties: Properties to validate
        is_user_created: Whether this is a user-created entity
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    
    try:
        entity_type_enum = EntityType(entity_type)
        required_props = ENTITY_REQUIRED_PROPERTIES.get(entity_type_enum, set())
        
        if is_user_created:
            optional_props = USER_ENTITY_OPTIONAL_PROPERTIES.get(entity_type_enum, set())
        else:
            optional_props = ENTITY_OPTIONAL_PROPERTIES.get(entity_type_enum, set())
        
        # Check required properties
        for prop in required_props:
            if prop not in properties:
                errors.append(f"Missing required property: {prop}")
            elif not properties[prop]:
                errors.append(f"Required property \"{prop}\" cannot be empty")
        
        # Check for invalid properties
        all_valid_props = required_props | optional_props
        for prop in properties:
            if prop not in all_valid_props and prop not in ["id", "created_at", "updated_at"]:
                if is_user_created and prop in ["chunk_count", "chunk_ids"]:
                    errors.append(f"Property \"{prop}\" is not allowed for user-created entities")
                
    except ValueError:
        errors.append(f"Invalid entity type: {entity_type}")
    
    return errors

def validate_relationship(from_entity_type: str, to_entity_type: str, 
                         relationship_type: str) -> List[str]:
    """
    Validate a relationship between entity types.
    
    Args:
        from_entity_type: Source entity type
        to_entity_type: Target entity type
        relationship_type: Relationship type
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    
    # Check if entity types are valid
    if not is_valid_entity_type(from_entity_type):
        errors.append(f"Invalid source entity type: {from_entity_type}")
    
    if not is_valid_entity_type(to_entity_type):
        errors.append(f"Invalid target entity type: {to_entity_type}")
    
    if not is_valid_relationship_type(relationship_type):
        errors.append(f"Invalid relationship type: {relationship_type}")
    
    if errors:
        return errors
    
    # Check if relationship combination is valid
    from_enum = EntityType(from_entity_type)
    to_enum = EntityType(to_entity_type)
    rel_enum = RelationshipType(relationship_type)
    
    valid_combinations = VALID_RELATIONSHIP_COMBINATIONS.get(from_enum, {})
    valid_relationships = valid_combinations.get(to_enum, set())
    
    if valid_relationships and rel_enum not in valid_relationships:
        errors.append(
            f"Invalid relationship '{relationship_type}' between "
            f"{from_entity_type} and {to_entity_type}"
        )
    
    return errors

def get_valid_entity_types() -> List[str]:
    """
    Get all valid entity types.
    
    Returns:
        List[str]: List of valid entity types
    """
    return [et.value for et in EntityType]

def get_valid_relationship_types() -> List[str]:
    """
    Get all valid relationship types.
    
    Returns:
        List[str]: List of valid relationship types
    """
    return [rt.value for rt in RelationshipType]

def get_entity_schema(entity_type: str, is_user_created: bool = False) -> Dict[str, Any]:
    """
    Get the schema for an entity type.
    
    Args:
        entity_type: Entity type
        is_user_created: Whether to get schema for user-created entities
        
    Returns:
        Dict[str, Any]: Schema information
    """
    try:
        entity_type_enum = EntityType(entity_type)
        required_props = ENTITY_REQUIRED_PROPERTIES.get(entity_type_enum, set())
        
        if is_user_created:
            optional_props = USER_ENTITY_OPTIONAL_PROPERTIES.get(entity_type_enum, set())
        else:
            optional_props = ENTITY_OPTIONAL_PROPERTIES.get(entity_type_enum, set())
        
        return {
            "entity_type": entity_type,
            "is_user_created": is_user_created,
            "required_properties": list(required_props),
            "optional_properties": list(optional_props)
        }
    except ValueError:
        return None

def get_relationship_schema() -> Dict[str, Any]:
    """
    Get the relationship schema information.
    
    Returns:
        Dict[str, Any]: Relationship schema
    """
    return {
        "relationship_types": [rt.value for rt in RelationshipType],
        "valid_combinations": {
            from_type.value: {
                to_type.value: [rt.value for rt in relationships]
                for to_type, relationships in to_types.items()
            }
            for from_type, to_types in VALID_RELATIONSHIP_COMBINATIONS.items()
        }
    } 