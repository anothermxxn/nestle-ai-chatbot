from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

from ..models.entity import EntityType, create_brand_entity, create_topic_entity, create_product_entity, create_recipe_entity
from ..models.relationship import RelationshipType, create_relationship
from ..services.cosmos_service import CosmosGraphClient
from ..services.count_service import CountStatisticsService
from ..validation.validators import (
    is_valid_entity_type, is_valid_relationship_type,
    validate_entity_properties, validate_relationship,
    get_valid_entity_types, get_valid_relationship_types,
    get_entity_schema, get_relationship_schema
)

router = APIRouter(prefix="/api/graph", tags=["graph"])

# Pydantic models for request/response
class EntityRequest(BaseModel):
    """Request model for creating/updating entities."""
    entity_type: str = Field(..., description="Type of entity (Brand, Topic, Product, Recipe)")
    properties: Dict[str, Any] = Field(..., description="Entity properties")
    is_user_created: bool = Field(default=True, description="Whether this is a user-created entity")

class EntityResponse(BaseModel):
    """Response model for entity operations."""
    id: str
    entity_type: str
    properties: Dict[str, Any]
    is_user_created: bool
    created_at: str
    updated_at: str

class RelationshipRequest(BaseModel):
    """Request model for creating relationships."""
    from_entity_id: str = Field(..., description="Source entity ID")
    to_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")
    weight: float = Field(default=1.0, description="Relationship weight", ge=0.0, le=1.0)
    is_user_created: bool = Field(default=True, description="Whether this is a user-created relationship")

class RelationshipResponse(BaseModel):
    """Response model for relationship operations."""
    id: str
    from_entity_id: str
    to_entity_id: str
    relationship_type: str
    properties: Dict[str, Any]
    weight: float
    is_user_created: bool
    created_at: str
    updated_at: str

class ValidationRequest(BaseModel):
    """Request model for validation operations."""
    entity_type: str
    properties: Dict[str, Any]
    is_user_created: bool = Field(default=True, description="Whether this is a user-created entity")

class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""
    total_entities: int
    total_relationships: int
    entity_counts: Dict[str, int]
    relationship_counts: Dict[str, int]

class CountStatsResponse(BaseModel):
    """Response model for count statistics."""
    entity_counts: Dict[str, int]
    
class ProductCountStatsResponse(BaseModel):
    """Response model for product-specific count statistics."""
    total_products: int
    by_brand: Dict[str, int]
    
class CategoryCountStatsResponse(BaseModel):
    """Response model for category-based count statistics."""
    by_category: Dict[str, int]
    recipe_stats: Dict[str, Any]

# Dependency to get graph client
async def get_graph_client() -> CosmosGraphClient:
    """Get graph client instance."""
    return CosmosGraphClient()

# Dependency to get count service
async def get_count_service() -> CountStatisticsService:
    """Get count statistics service instance."""
    return CountStatisticsService()

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for the graph service."""
    return {"status": "healthy", "service": "graph"}

# Schema endpoints
@router.get("/schema/entity-types")
async def get_entity_types():
    """
    Get all valid entity types and their schemas.
    
    Returns:
        dict: Entity types and schemas for both system and user-created entities
    """
    try:
        entity_types = get_valid_entity_types()
        schemas = {}
        
        for entity_type in entity_types:
            # Get schema for system-created entities
            system_schema = get_entity_schema(entity_type, is_user_created=False)
            # Get schema for user-created entities
            user_schema = get_entity_schema(entity_type, is_user_created=True)
            
            schemas[entity_type] = {
                "system_created": system_schema,
                "user_created": user_schema
            }
        
        return {
            "entity_types": entity_types,
            "schemas": schemas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/schema/relationship-types")
async def get_relationship_types():
    """
    Get all valid relationship types and their schemas.
    
    Returns:
        dict: Relationship types and schema information
    """
    try:
        relationship_types = get_valid_relationship_types()
        schema = get_relationship_schema()
        
        return {
            "relationship_types": relationship_types,
            "schema": schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Validation endpoints
@router.post("/validate/entity")
async def validate_entity_endpoint(request: ValidationRequest):
    """
    Validate entity properties before creation.
    
    Args:
        request: Validation request
        
    Returns:
        dict: Validation result
    """
    try:
        # Validate entity type
        if not is_valid_entity_type(request.entity_type):
            return {
                "valid": False,
                "errors": [f"Invalid entity type: {request.entity_type}"]
            }
        
        # Validate properties
        errors = validate_entity_properties(
            request.entity_type, 
            request.properties, 
            request.is_user_created
        )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/validate/relationship")
async def validate_relationship_endpoint(
    from_entity_type: str,
    to_entity_type: str,
    relationship_type: str
):
    """
    Validate relationship before creation.
    
    Args:
        from_entity_type: Source entity type
        to_entity_type: Target entity type  
        relationship_type: Relationship type
        
    Returns:
        dict: Validation result
    """
    try:
        errors = validate_relationship(from_entity_type, to_entity_type, relationship_type)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Entity endpoints
@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    entity_request: EntityRequest,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Create a new entity.
    
    Args:
        entity_request: Entity creation request
        graph_client: Graph client instance
        
    Returns:
        EntityResponse: Created entity data
    """
    try:
        # Validate entity type
        if not is_valid_entity_type(entity_request.entity_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type: {entity_request.entity_type}"
            )
        
        # Validate properties
        prop_errors = validate_entity_properties(
            entity_request.entity_type, 
            entity_request.properties,
            entity_request.is_user_created
        )
        if prop_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Validation errors: {', '.join(prop_errors)}"
            )
        
        # Create entity
        entity_type_enum = EntityType(entity_request.entity_type)
        if entity_type_enum == EntityType.BRAND:
            entity = create_brand_entity(
                name=entity_request.properties.get("name", ""),
                chunk_ids=entity_request.properties.get("chunk_ids", []),
                **{k: v for k, v in entity_request.properties.items() if k not in ["name", "chunk_ids"]}
            )
        elif entity_type_enum == EntityType.TOPIC:
            entity = create_topic_entity(
                name=entity_request.properties.get("name", ""),
                category=entity_request.properties.get("category", "user_defined"),
                chunk_ids=entity_request.properties.get("chunk_ids", []),
                **{k: v for k, v in entity_request.properties.items() if k not in ["name", "category", "chunk_ids"]}
            )
        elif entity_type_enum == EntityType.PRODUCT:
            entity = create_product_entity(
                name=entity_request.properties.get("name", ""),
                brand=entity_request.properties.get("brand", ""),
                chunk_ids=entity_request.properties.get("chunk_ids", []),
                **{k: v for k, v in entity_request.properties.items() if k not in ["name", "brand", "chunk_ids"]}
            )
        elif entity_type_enum == EntityType.RECIPE:
            entity = create_recipe_entity(
                title=entity_request.properties.get("title", ""),
                chunk_ids=entity_request.properties.get("chunk_ids", []),
                **{k: v for k, v in entity_request.properties.items() if k not in ["title", "chunk_ids"]}
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported entity type: {entity_request.entity_type}"
            )
        
        entity.is_user_created = entity_request.is_user_created
        
        if entity_request.is_user_created:
            # For user-created entities, generate a unique ID
            name_part = entity_request.properties.get("name") or entity_request.properties.get("title", "")
            if name_part:
                safe_name = name_part.lower().replace(" ", "_").replace("-", "_")[:20]
                entity.id = f"user_{entity_request.entity_type.lower()}_{safe_name}_{uuid.uuid4().hex[:8]}"
            else:
                entity.id = f"user_{entity_request.entity_type.lower()}_{uuid.uuid4().hex[:8]}"

        # Save to database
        success = await graph_client.create_entity(entity)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to create entity. Entity may already exist."
            )
        
        return EntityResponse(
            id=entity.id,
            entity_type=entity_request.entity_type,
            properties=entity_request.properties,
            is_user_created=entity_request.is_user_created,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    entity_type: str,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Get an entity by ID and type.
    
    Args:
        entity_id: Entity ID
        entity_type: Entity type
        graph_client: Graph client instance
        
    Returns:
        EntityResponse: Entity data
    """
    try:
        # Validate entity type
        if not is_valid_entity_type(entity_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type: {entity_type}"
            )
        
        # Convert to enum and get entity
        entity_type_enum = EntityType(entity_type)
        entity = await graph_client.get_entity(entity_id, entity_type_enum)
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return EntityResponse(
            id=entity.id,
            entity_type=entity_type,
            properties=entity.properties,
            is_user_created=entity.is_user_created,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/entities/{entity_id}")
async def update_entity(
    entity_id: str,
    entity_type: str,
    properties: Dict[str, Any],
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Update an entity's properties.
    
    Args:
        entity_id: Entity ID
        entity_type: Entity type (must be one of: Brand, Topic, Product, Recipe)
        properties: Properties to update
        graph_client: Graph client instance
        
    Returns:
        dict: Success message
    """
    try:
        # Validate entity type
        if not is_valid_entity_type(entity_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type: {entity_type}"
            )
        
        # Validate properties (assume user-created for updates)
        prop_errors = validate_entity_properties(entity_type, properties, True)
        if prop_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Validation errors: {', '.join(prop_errors)}"
            )
        
        # Convert to enum and update entity
        entity_type_enum = EntityType(entity_type)
        success = await graph_client.update_entity(entity_id, entity_type_enum, properties)
        
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found or update failed")
        
        return {"message": "Entity updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    entity_type: str,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Delete an entity and its relationships.
    
    Args:
        entity_id: Entity ID
        entity_type: Entity type (must be one of: Brand, Topic, Product, Recipe)
        graph_client: Graph client instance
        
    Returns:
        dict: Success message
    """
    try:
        # Validate entity type
        if not is_valid_entity_type(entity_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type: {entity_type}"
            )
        
        # Convert to enum and delete entity
        entity_type_enum = EntityType(entity_type)
        success = await graph_client.delete_entity(entity_id, entity_type_enum)
        
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found or deletion failed")
        
        return {"message": "Entity deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[str] = None,
    limit: int = 100,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    List entities by type.
    
    Args:
        entity_type: Optional entity type filter (must be one of: Brand, Topic, Product, Recipe)
        limit: Maximum number of entities to return
        graph_client: Graph client instance
        
    Returns:
        List[EntityResponse]: List of entities
    """
    try:
        if entity_type:
            # Validate entity type
            if not is_valid_entity_type(entity_type):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid entity type: {entity_type}"
                )
            
            # Get entities of specific type
            entity_type_enum = EntityType(entity_type)
            entities = await graph_client.find_entities_by_type(entity_type_enum, limit)
        else:
            # Get all entities
            entities = []
            for et in EntityType:
                type_entities = await graph_client.find_entities_by_type(et, limit)
                entities.extend(type_entities)
        
        return [
            EntityResponse(
                id=entity.id,
                entity_type=entity.entity_type.value,
                properties=entity.properties,
                is_user_created=entity.is_user_created,
                created_at=entity.created_at.isoformat(),
                updated_at=entity.updated_at.isoformat()
            )
            for entity in entities
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/entities/{entity_id}/relationships", response_model=List[RelationshipResponse])
async def get_entity_relationships(
    entity_id: str,
    direction: str = "both",
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Get relationships for an entity.
    
    Args:
        entity_id: Entity ID
        direction: Relationship direction (in, out, both)
        graph_client: Graph client instance
        
    Returns:
        List[RelationshipResponse]: List of relationships
    """
    try:
        if direction not in ["in", "out", "both"]:
            raise HTTPException(
                status_code=400,
                detail="Direction must be 'in', 'out', or 'both'"
            )
        
        relationships = await graph_client.get_entity_relationships(entity_id, direction)
        
        return [
            RelationshipResponse(
                id=rel.id,
                from_entity_id=rel.from_entity_id,
                to_entity_id=rel.to_entity_id,
                relationship_type=rel.relationship_type.value,
                properties=rel.properties,
                weight=rel.weight,
                is_user_created=rel.is_user_created,
                created_at=rel.created_at.isoformat(),
                updated_at=rel.updated_at.isoformat()
            )
            for rel in relationships
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Relationship endpoints
@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship_endpoint(
    relationship_request: RelationshipRequest,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Create a new relationship between entities.
    
    Args:
        relationship_request: Relationship creation request
        graph_client: Graph client instance
        
    Returns:
        RelationshipResponse: Created relationship
    """
    try:
        # Validate relationship type
        if not is_valid_relationship_type(relationship_request.relationship_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid relationship type: {relationship_request.relationship_type}"
            )
        
        # Verify that both entities exist
        from_entity = await graph_client.get_entity_by_id(relationship_request.from_entity_id)
        to_entity = await graph_client.get_entity_by_id(relationship_request.to_entity_id)
        
        if not from_entity:
            raise HTTPException(
                status_code=404,
                detail=f"Source entity not found: {relationship_request.from_entity_id}"
            )
        
        if not to_entity:
            raise HTTPException(
                status_code=404,
                detail=f"Target entity not found: {relationship_request.to_entity_id}"
            )
        
        # Validate relationship combination
        errors = validate_relationship(
            from_entity.entity_type.value,
            to_entity.entity_type.value,
            relationship_request.relationship_type
        )
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid relationship: {', '.join(errors)}"
            )
        
        # Create relationship
        relationship = create_relationship(
            from_entity_id=relationship_request.from_entity_id,
            to_entity_id=relationship_request.to_entity_id,
            relationship_type=RelationshipType(relationship_request.relationship_type),
            **relationship_request.properties
        )
        
        # Set weight and user-created flag
        relationship.weight = relationship_request.weight
        relationship.is_user_created = relationship_request.is_user_created
        
        # Save to database
        success = await graph_client.create_relationship(relationship)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to create relationship"
            )
        
        return RelationshipResponse(
            id=relationship.id,
            from_entity_id=relationship.from_entity_id,
            to_entity_id=relationship.to_entity_id,
            relationship_type=relationship.relationship_type.value,
            properties=relationship.properties,
            weight=relationship.weight,
            is_user_created=relationship.is_user_created,
            created_at=relationship.created_at.isoformat(),
            updated_at=relationship.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/relationships/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship(
    relationship_id: str,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Get a relationship by ID.
    
    Args:
        relationship_id: Relationship ID
        graph_client: Graph client instance
        
    Returns:
        RelationshipResponse: Relationship details
    """
    try:
        relationship = await graph_client.get_relationship_by_id(relationship_id)
        
        if not relationship:
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        return RelationshipResponse(
            id=relationship.id,
            from_entity_id=relationship.from_entity_id,
            to_entity_id=relationship.to_entity_id,
            relationship_type=relationship.relationship_type.value,
            properties=relationship.properties,
            weight=relationship.weight,
            is_user_created=relationship.is_user_created,
            created_at=relationship.created_at.isoformat(),
            updated_at=relationship.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/relationships/{relationship_id}")
async def update_relationship(
    relationship_id: str,
    properties: Dict[str, Any] = None,
    weight: float = None,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Update a relationship's properties and/or weight.
    
    Args:
        relationship_id: Relationship ID
        properties: Properties to update (optional)
        weight: New weight for the relationship (optional)
        graph_client: Graph client instance
        
    Returns:
        dict: Success message
    """
    try:
        # Validate weight if provided
        if weight is not None and (weight < 0.0 or weight > 1.0):
            raise HTTPException(
                status_code=400,
                detail="Weight must be between 0.0 and 1.0"
            )
        
        # Update relationship
        success = await graph_client.update_relationship(
            relationship_id=relationship_id,
            properties=properties or {},
            weight=weight
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found or update failed")
        
        return {"message": "Relationship updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: str,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    Delete a relationship.
    
    Args:
        relationship_id: Relationship ID
        graph_client: Graph client instance
        
    Returns:
        dict: Success message
    """
    try:
        success = await graph_client.delete_relationship(relationship_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found or deletion failed")
        
        return {"message": "Relationship deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/relationships", response_model=List[RelationshipResponse])
async def list_relationships(
    limit: int = 100,
    graph_client: CosmosGraphClient = Depends(get_graph_client)
):
    """
    List all relationships.
    
    Args:
        limit: Maximum number of relationships to return
        graph_client: Graph client instance
        
    Returns:
        List[RelationshipResponse]: List of relationships
    """
    try:
        relationships = await graph_client.get_all_relationships(limit)
        
        return [
            RelationshipResponse(
                id=rel.id,
                from_entity_id=rel.from_entity_id,
                to_entity_id=rel.to_entity_id,
                relationship_type=rel.relationship_type.value,
                properties=rel.properties,
                weight=rel.weight,
                is_user_created=rel.is_user_created,
                created_at=rel.created_at.isoformat(),
                updated_at=rel.updated_at.isoformat()
            )
            for rel in relationships
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Count Statistics Endpoints
@router.get("/stats", response_model=CountStatsResponse)
async def get_count_stats(
    count_service: CountStatisticsService = Depends(get_count_service)
):
    """
    Get entity count statistics from the graph database.
    
    Args:
        count_service: Count statistics service instance
        
    Returns:
        CountStatsResponse: Entity counts by type
    """
    try:
        entity_counts = await count_service.get_entity_counts()
        
        return CountStatsResponse(
            entity_counts=entity_counts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stats/products", response_model=ProductCountStatsResponse)
async def get_product_count_stats(
    count_service: CountStatisticsService = Depends(get_count_service)
):
    """
    Get product-specific count statistics.
    
    Args:
        count_service: Count statistics service instance
        
    Returns:
        ProductCountStatsResponse: Product counts by brand
    """
    try:
        brand_counts = await count_service.get_product_counts_by_brand()
        total_products = sum(brand_counts.values())
        
        return ProductCountStatsResponse(
            total_products=total_products,
            by_brand=brand_counts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/stats/categories", response_model=CategoryCountStatsResponse)
async def get_category_count_stats(
    count_service: CountStatisticsService = Depends(get_count_service)
):
    """
    Get category-based count statistics.
    
    Args:
        count_service: Count statistics service instance
        
    Returns:
        CategoryCountStatsResponse: Product counts by category and recipe statistics
    """
    try:
        category_counts = await count_service.get_product_counts_by_category()
        recipe_stats = await count_service.get_recipe_counts()
        
        return CategoryCountStatsResponse(
            by_category=category_counts,
            recipe_stats=recipe_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")