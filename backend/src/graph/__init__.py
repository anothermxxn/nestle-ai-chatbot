# Dynamic import to handle both local development and Docker environments
try:
    from backend.config import (
        ENTITY_TYPES,
        RELATIONSHIP_TYPES,
        ENTITIES_CONTAINER_NAME,
        RELATIONSHIPS_CONTAINER_NAME
    )
except ImportError:
    from config import (
        ENTITY_TYPES,
        RELATIONSHIP_TYPES,
        ENTITIES_CONTAINER_NAME,
        RELATIONSHIPS_CONTAINER_NAME
    )

from .cosmos_client import CosmosGraphClient
from .models import EntityType, RelationshipType, Entity, Relationship

__all__ = [
    "COSMOS_CONFIG",
    "ENTITIES_CONTAINER_NAME",
    "RELATIONSHIPS_CONTAINER_NAME",
    "ENTITY_TYPES",
    "RELATIONSHIP_TYPES",
    "CONTAINER_CONFIGS",
    "CosmosGraphClient",
    "EntityType",
    "RelationshipType",
    "Entity",
    "Relationship"
] 