import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.config import (
    DEFAULT_VECTOR_CHUNKS_FILE,
    COSMOS_CONFIG,
    ENTITIES_CONTAINER_NAME,
    RELATIONSHIPS_CONTAINER_NAME,
    validate_config,
    setup_logging
)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "src"))
from graph.services.cosmos_service import CosmosGraphClient
from graph.models.entity import (
    extract_entities_from_chunks,
    EntityType,
)
from graph.models.relationship import create_entity_relationships

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

class CosmosSetup:
    """Setup class for initializing Cosmos DB graph database."""
    
    def __init__(self):
        """Initialize the setup with a Cosmos client."""
        try:
            validate_config()
            self.client = CosmosGraphClient()
            logger.info("Cosmos DB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {str(e)}")
            raise
    
    async def verify_containers(self) -> bool:
        """Verify that the required containers exist and are accessible."""
        logger.info("\nVerifying Cosmos DB containers...")
        
        try:
            health_status = await self.client.health_check()
            if not health_status:
                logger.error("Health check failed")
                return False
            
            logger.info(f"Database: {COSMOS_CONFIG['database_name']}")
            logger.info(f"Entities container: {ENTITIES_CONTAINER_NAME}")
            logger.info(f"Relationships container: {RELATIONSHIPS_CONTAINER_NAME}")
            
            return True
            
        except Exception as e:
            logger.error(f"Container verification failed: {str(e)}")
            return False
    
    async def clear_existing_data(self) -> bool:
        """Clear all existing entities and relationships."""
        logger.info("\nClearing existing data...")
        
        try:
            for entity_type in EntityType:
                entities = await self.client.find_entities_by_type(entity_type, limit=1000)
                for entity in entities:
                    success = await self.client.delete_entity(entity.id, entity.entity_type)
                    if not success:
                        logger.error(f"  Failed to delete entity: {entity.id}")
            
            logger.info("Data clearing completed")
            return True
            
        except Exception as e:
            logger.error(f"Data clearing failed: {str(e)}")
            return False
    
    async def load_processed_chunks(self) -> List[Dict[str, Any]]:
        """Load processed content chunks from the JSON file."""
        chunks_file = DEFAULT_VECTOR_CHUNKS_FILE
        
        if not os.path.exists(chunks_file):
            logger.error(f"No processed chunks found at {chunks_file}")
            logger.info("   Please run the data processing first.")
            return []
        
        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            logger.info(f"Loaded {len(chunks)} processed chunks")
            return chunks
        except Exception as e:
            logger.error(f"Failed to load chunks: {str(e)}")
            return []
    
    async def populate_entities(self, chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Extract and create entities from processed chunks."""
        logger.info("\nExtracting and creating entities...")
        
        try:
            # Extract entities from chunks
            entities_by_type = extract_entities_from_chunks(chunks)
            
            # Create entities in Cosmos DB
            created_entities = {}
            total_entities = 0
            
            for entity_type, entities_list in entities_by_type.items():
                created_entities[entity_type] = {}
                logger.info(f"\n  Creating {len(entities_list)} {entity_type} entities...")
                
                for entity in entities_list:
                    success = await self.client.create_entity(entity)
                    if success:
                        created_entities[entity_type][entity.id] = entity
                        total_entities += 1
                    else:
                        logger.error(f"    Failed: {entity.id}")
            
            logger.info(f"\nCreated {total_entities} entities total")
            return created_entities
            
        except Exception as e:
            logger.error(f"Entity creation failed: {str(e)}")
            return {}
    
    async def populate_relationships(self, entities: Dict[str, Dict[str, Any]]) -> int:
        """Create relationships between entities."""
        logger.info("\nCreating relationships...")
        
        try:
            # Generate relationships
            relationships = create_entity_relationships(entities)
            
            # Create relationships in Cosmos DB
            created_count = 0
            
            for relationship in relationships:
                success = await self.client.create_relationship(relationship)
                if success:
                    created_count += 1
                else:
                    logger.error(f"    Failed: {relationship.relationship_type.value} "
                          f"({relationship.from_entity_id} -> {relationship.to_entity_id})")
            
            logger.info(f"\nCreated {created_count} relationships total")
            return created_count
            
        except Exception as e:
            logger.error(f"Relationship creation failed: {str(e)}")
            return 0
    
    async def setup_database(self, clear_existing: bool = False):
        """Complete database setup process."""
        logger.info("Starting Cosmos DB Graph Database Setup")
        logger.info("=" * 50)
        
        # Verify containers
        if not await self.verify_containers():
            return False
        
        # Clear existing data if requested
        if clear_existing:
            if not await self.clear_existing_data():
                return False
        
        # Populate with data
        chunks = await self.load_processed_chunks()
        if not chunks:
            logger.warning("No data to populate. Database setup completed with empty containers.")
            return True
        
        # Create entities
        entities = await self.populate_entities(chunks)
        if not entities:
            logger.error("Failed to create entities")
            return False
        
        # Create relationships
        relationship_count = await self.populate_relationships(entities)
        if relationship_count == 0:
            logger.warning("No relationships created")
        
        logger.info("\nCosmos DB Graph Database setup completed successfully!")
        return True

async def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Cosmos DB Graph Database")
    parser.add_argument("--clear", action="store_true", 
                       help="Clear existing data before setup")
    
    args = parser.parse_args()
    
    try:
        setup = CosmosSetup()
        success = await setup.setup_database(
            clear_existing=args.clear,
        )
        
        if success:
            logger.info("\nSetup completed successfully!")
            return 0
        else:
            logger.error("\nSetup failed!")
            return 1
            
    except Exception as e:
        logger.error(f"\nSetup failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 