import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import ContainerProxy
from azure.cosmos.database import DatabaseProxy

try:
    from backend.config.database import (
        COSMOS_CONFIG,
        ENTITY_TYPES, 
        ENTITIES_CONTAINER_NAME,
        RELATIONSHIPS_CONTAINER_NAME,
        CONTAINER_CONFIGS,
        validate_config
    )
    from backend.src.graph.models.entity import Entity, EntityType
    from backend.src.graph.models.relationship import Relationship, RelationshipType
except ImportError:
    from config.database import (
        COSMOS_CONFIG,
        ENTITY_TYPES, 
        ENTITIES_CONTAINER_NAME,
        RELATIONSHIPS_CONTAINER_NAME,
        CONTAINER_CONFIGS,
        validate_config
    )
    from src.graph.models.entity import Entity, EntityType
    from src.graph.models.relationship import Relationship, RelationshipType

logger = logging.getLogger(__name__)

class CosmosGraphClient:
    """
    Simplified client for Azure Cosmos DB NoSQL with basic graph operations.
    
    Provides functionality for:
    - Entity CRUD operations
    - Relationship CRUD operations  
    - Basic graph traversal queries
    - Container management
    """
    
    def __init__(self):
        """Initialize the Cosmos DB client."""
        try:
            # Validate configuration
            validate_config()
            
            # Initialize Cosmos client
            self.cosmos_client = CosmosClient(
                url=COSMOS_CONFIG["endpoint"],
                credential=COSMOS_CONFIG["key"]
            )
            
            # Get database reference
            self.database = self._get_or_create_database()
            
            # Get container references
            self.entities_container = self._get_or_create_container(ENTITIES_CONTAINER_NAME)
            self.relationships_container = self._get_or_create_container(RELATIONSHIPS_CONTAINER_NAME)
            
            logger.info("Successfully initialized CosmosGraphClient")
            
        except Exception as e:
            logger.error(f"Failed to initialize CosmosGraphClient: {str(e)}")
            raise
    
    def _get_or_create_database(self) -> DatabaseProxy:
        """Get or create the database."""
        try:
            database = self.cosmos_client.create_database_if_not_exists(
                id=COSMOS_CONFIG["database_name"]
            )
            logger.info(f"Database '{COSMOS_CONFIG['database_name']}' ready")
            return database
        except Exception as e:
            logger.error(f"Failed to create/get database: {str(e)}")
            raise
    
    def _get_or_create_container(self, container_name: str) -> ContainerProxy:
        """Get or create a container."""
        try:
            config = CONTAINER_CONFIGS[container_name]
            container = self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path=config["partition_key"]),
                offer_throughput=config["throughput"]
            )
            logger.info(f"Container '{container_name}' ready")
            return container
        except Exception as e:
            logger.error(f"Failed to create/get container {container_name}: {str(e)}")
            raise
    
    # Entity Operations
    async def create_entity(self, entity: Entity) -> bool:
        """
        Create a new entity in Cosmos DB.
        
        Args:
            entity (Entity): The entity to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate entity
            if not self._validate_entity(entity):
                return False
            
            # Convert to document format
            document = entity.to_cosmos_document()
            
            # Create in Cosmos DB
            self.entities_container.create_item(body=document)
            
            logger.info(f"Created entity: {entity.id} of type {entity.entity_type.value}")
            return True
            
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Entity {entity.id} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create entity {entity.id}: {str(e)}")
            return False
    
    async def get_entity(self, entity_id: str, entity_type: EntityType) -> Optional[Entity]:
        """
        Retrieve an entity by ID.
        
        Args:
            entity_id (str): The ID of the entity
            entity_type (EntityType): The type of the entity
            
        Returns:
            Optional[Entity]: The entity if found, None otherwise
        """
        try:
            item = self.entities_container.read_item(
                item=entity_id,
                partition_key=entity_type.value
            )
            return Entity.from_cosmos_document(item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Entity {entity_id} not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get entity {entity_id}: {str(e)}")
            return None
    
    async def update_entity(self, entity_id: str, entity_type: EntityType, 
                           properties: Dict[str, Any]) -> bool:
        """
        Update an entity's properties.
        
        Args:
            entity_id (str): The ID of the entity
            entity_type (EntityType): The type of the entity
            properties (Dict[str, Any]): Properties to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get existing item
            existing_item = self.entities_container.read_item(
                item=entity_id,
                partition_key=entity_type.value
            )
            
            # Update properties
            existing_item.update(properties)
            existing_item["updated_at"] = datetime.utcnow().isoformat()
            
            # Replace item
            self.entities_container.replace_item(
                item=entity_id,
                body=existing_item
            )
            
            logger.info(f"Updated entity: {entity_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"Entity {entity_id} not found for update")
            return False
        except Exception as e:
            logger.error(f"Failed to update entity {entity_id}: {str(e)}")
            return False
    
    async def delete_entity(self, entity_id: str, entity_type: EntityType) -> bool:
        """
        Delete an entity and its relationships.
        
        Args:
            entity_id (str): The ID of the entity
            entity_type (EntityType): The type of the entity
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First delete all relationships involving this entity
            await self._delete_entity_relationships(entity_id)
            
            # Then delete the entity
            self.entities_container.delete_item(
                item=entity_id,
                partition_key=entity_type.value
            )
            
            logger.info(f"Deleted entity: {entity_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Entity {entity_id} not found for deletion")
            return False
        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
            return False
    
    # Relationship Operations
    async def create_relationship(self, relationship: Relationship) -> bool:
        """
        Create a new relationship in Cosmos DB.
        
        Args:
            relationship (Relationship): The relationship to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to document format
            document = relationship.to_cosmos_document()
            
            # Create in Cosmos DB
            self.relationships_container.create_item(body=document)
            
            logger.info(f"Created relationship: {relationship.from_entity_id} -[{relationship.relationship_type.value}]-> {relationship.to_entity_id}")
            return True
            
        except exceptions.CosmosResourceExistsError:
            logger.warning(f"Relationship {relationship.id} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create relationship {relationship.id}: {str(e)}")
            return False
    
    async def get_entity_relationships(self, entity_id: str, 
                                     direction: str = "both") -> List[Relationship]:
        """
        Get all relationships for an entity.
        
        Args:
            entity_id (str): The ID of the entity
            direction (str): "in", "out", or "both"
            
        Returns:
            List[Relationship]: List of relationships
        """
        try:
            if direction == "out":
                query = "SELECT * FROM c WHERE c.from_entity_id = @entity_id"
            elif direction == "in":
                query = "SELECT * FROM c WHERE c.to_entity_id = @entity_id"
            else:  # both
                query = "SELECT * FROM c WHERE c.from_entity_id = @entity_id OR c.to_entity_id = @entity_id"
            
            items = list(self.relationships_container.query_items(
                query=query,
                parameters=[{"name": "@entity_id", "value": entity_id}],
                enable_cross_partition_query=True
            ))
            
            relationships = []
            for item in items:
                try:
                    relationships.append(Relationship.from_cosmos_document(item))
                except Exception as e:
                    logger.warning(f"Failed to parse relationship: {e}")
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to get relationships for entity {entity_id}: {str(e)}")
            return []

    async def get_relationship_by_id(self, relationship_id: str) -> Optional[Relationship]:
        """
        Get a relationship by ID.
        
        Args:
            relationship_id (str): The ID of the relationship
            
        Returns:
            Optional[Relationship]: The relationship if found, None otherwise
        """
        try:
            query = "SELECT * FROM c WHERE c.id = @relationship_id"
            
            items = list(self.relationships_container.query_items(
                query=query,
                parameters=[{"name": "@relationship_id", "value": relationship_id}],
                enable_cross_partition_query=True
            ))
            
            if items:
                return Relationship.from_cosmos_document(items[0])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get relationship by ID {relationship_id}: {str(e)}")
            return None

    async def update_relationship(self, relationship_id: str, 
                                properties: Dict[str, Any], 
                                weight: Optional[float] = None) -> bool:
        """
        Update a relationship's properties and/or weight.
        
        Args:
            relationship_id (str): The ID of the relationship
            properties (Dict[str, Any]): Properties to update
            weight (Optional[float]): New weight for the relationship
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get existing relationship
            existing_rel = await self.get_relationship_by_id(relationship_id)
            if not existing_rel:
                logger.error(f"Relationship {relationship_id} not found")
                return False
            
            # Update properties
            updated_properties = existing_rel.properties.copy()
            updated_properties.update(properties)
            
            # Update weight if provided
            updated_weight = weight if weight is not None else existing_rel.weight
            
            # Create updated document
            updated_document = {
                "id": relationship_id,
                "relationship_type": existing_rel.relationship_type.value,
                "from_entity_id": existing_rel.from_entity_id,
                "to_entity_id": existing_rel.to_entity_id,
                "weight": updated_weight,
                "created_at": existing_rel.created_at.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                **updated_properties
            }
            
            # Replace in Cosmos DB
            self.relationships_container.replace_item(
                item=relationship_id,
                body=updated_document
            )
            
            logger.info(f"Updated relationship: {relationship_id}")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"Relationship {relationship_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update relationship {relationship_id}: {str(e)}")
            return False

    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship by ID.
        
        Args:
            relationship_id (str): The ID of the relationship to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the relationship first to log the deletion
            relationship = await self.get_relationship_by_id(relationship_id)
            if not relationship:
                logger.warning(f"Relationship {relationship_id} not found")
                return False
            
            # Delete from Cosmos DB
            self.relationships_container.delete_item(
                item=relationship_id,
                partition_key=relationship_id
            )
            
            logger.info(f"Deleted relationship: {relationship_id} ({relationship.from_entity_id} -[{relationship.relationship_type.value}]-> {relationship.to_entity_id})")
            return True
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Relationship {relationship_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to delete relationship {relationship_id}: {str(e)}")
            return False

    async def get_all_relationships(self, limit: int = 100) -> List[Relationship]:
        """
        Get all relationships in the database.
        
        Args:
            limit (int): Maximum number of relationships to return
            
        Returns:
            List[Relationship]: List of relationships
        """
        try:
            query = f"SELECT TOP {limit} * FROM c"
            
            items = list(self.relationships_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            relationships = []
            for item in items:
                try:
                    relationships.append(Relationship.from_cosmos_document(item))
                except Exception as e:
                    logger.warning(f"Failed to parse relationship: {e}")
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to get all relationships: {str(e)}")
            return []
    
    # Query Operations
    async def get_entity_by_id(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by ID without knowing its type.
        
        Args:
            entity_id (str): The ID of the entity
            
        Returns:
            Optional[Entity]: The entity if found, None otherwise
        """
        try:
            query = "SELECT * FROM c WHERE c.id = @entity_id"
            
            items = list(self.entities_container.query_items(
                query=query,
                parameters=[{"name": "@entity_id", "value": entity_id}],
                enable_cross_partition_query=True
            ))
            
            if items:
                return Entity.from_cosmos_document(items[0])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get entity by ID {entity_id}: {str(e)}")
            return None

    async def find_entities_by_type(self, entity_type: EntityType, 
                                   limit: int = 100) -> List[Entity]:
        """
        Find entities by type.
        
        Args:
            entity_type (EntityType): The type of entities to find
            limit (int): Maximum number of entities to return
            
        Returns:
            List[Entity]: List of entities
        """
        try:
            query = f"SELECT TOP {limit} * FROM c WHERE c.entity_type = @entity_type"
            
            items = list(self.entities_container.query_items(
                query=query,
                parameters=[{"name": "@entity_type", "value": entity_type.value}],
                partition_key=entity_type.value
            ))
            
            entities = []
            for item in items:
                try:
                    entities.append(Entity.from_cosmos_document(item))
                except Exception as e:
                    logger.warning(f"Failed to parse entity: {e}")
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to find entities of type {entity_type.value}: {str(e)}")
            return []
    
    async def find_related_entities(self, entity_id: str, 
                                   relationship_type: RelationshipType,
                                   direction: str = "out") -> List[Entity]:
        """
        Find entities related to a given entity.
        
        Args:
            entity_id (str): The ID of the starting entity
            relationship_type (RelationshipType): The type of relationship
            direction (str): "in", "out", or "both"
            
        Returns:
            List[Entity]: List of related entities
        """
        try:
            # First get relationships
            if direction == "out":
                query = "SELECT * FROM c WHERE c.from_entity_id = @entity_id AND c.relationship_type = @rel_type"
                related_entity_field = "to_entity_id"
            elif direction == "in":
                query = "SELECT * FROM c WHERE c.to_entity_id = @entity_id AND c.relationship_type = @rel_type"
                related_entity_field = "from_entity_id"
            else:  # both
                query = "SELECT * FROM c WHERE (c.from_entity_id = @entity_id OR c.to_entity_id = @entity_id) AND c.relationship_type = @rel_type"
                related_entity_field = None
            
            relationships = list(self.relationships_container.query_items(
                query=query,
                parameters=[
                    {"name": "@entity_id", "value": entity_id},
                    {"name": "@rel_type", "value": relationship_type.value}
                ],
                enable_cross_partition_query=True
            ))
            
            # Get related entity IDs
            related_entity_ids = []
            for rel in relationships:
                if direction == "both":
                    # For both direction, add the other entity
                    if rel["from_entity_id"] == entity_id:
                        related_entity_ids.append(rel["to_entity_id"])
                    else:
                        related_entity_ids.append(rel["from_entity_id"])
                else:
                    related_entity_ids.append(rel[related_entity_field])
            
            # Get the actual entities
            entities = []
            for rel_id in related_entity_ids:
                # We need to query to find the entity since we don't know its type
                entity_query = "SELECT * FROM c WHERE c.id = @entity_id"
                entity_items = list(self.entities_container.query_items(
                    query=entity_query,
                    parameters=[{"name": "@entity_id", "value": rel_id}],
                    enable_cross_partition_query=True
                ))
                
                for item in entity_items:
                    try:
                        entities.append(Entity.from_cosmos_document(item))
                    except Exception as e:
                        logger.warning(f"Failed to parse entity: {e}")
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to find related entities for {entity_id}: {str(e)}")
            return []
    
    # Utility Methods
    def _validate_entity(self, entity: Entity) -> bool:
        """Validate an entity against the schema."""
        entity_type_name = entity.entity_type.value
        
        if entity_type_name not in ENTITY_TYPES:
            logger.error(f"Invalid entity type: {entity_type_name}")
            return False
        
        schema = ENTITY_TYPES[entity_type_name]
        required_props = schema.get("required", [])
        
        # Check required properties
        for prop in required_props:
            if prop not in entity.properties:
                logger.error(f"Missing required property '{prop}' for entity type {entity_type_name}")
                return False
        
        return True
    
    async def _delete_entity_relationships(self, entity_id: str):
        """Delete all relationships involving an entity."""
        try:
            # Find all relationships involving this entity
            relationships = await self.get_entity_relationships(entity_id, "both")
            
            # Delete each relationship
            for rel in relationships:
                try:
                    self.relationships_container.delete_item(
                        item=rel.id,
                        partition_key=rel.relationship_type.value
                    )
                except Exception as e:
                    logger.warning(f"Failed to delete relationship {rel.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to delete relationships for entity {entity_id}: {str(e)}")
    
    # Health check
    async def health_check(self) -> bool:
        """Check if the connection to Cosmos DB is healthy."""
        try:
            # Try to query a small result from entities container
            list(self.entities_container.query_items(
                query="SELECT TOP 1 * FROM c",
                enable_cross_partition_query=True
            ))
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False 