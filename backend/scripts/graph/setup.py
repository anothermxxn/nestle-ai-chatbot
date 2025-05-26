import asyncio
import json
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from utils.import_helper import setup_imports
setup_imports(__file__)
from config import (
    DEFAULT_VECTOR_CHUNKS_FILE,
    COSMOS_CONFIG,
    ENTITIES_CONTAINER_NAME,
    RELATIONSHIPS_CONTAINER_NAME,
    validate_config
)
from graph.cosmos_client import CosmosGraphClient
from graph.models import (
    extract_entities_from_chunks,
    create_entity_relationships,
    EntityType,
)

# Load environment variables
load_dotenv()

class CosmosSetup:
    """Setup class for initializing Cosmos DB graph database."""
    
    def __init__(self):
        """Initialize the setup with a Cosmos client."""
        try:
            validate_config()
            self.client = CosmosGraphClient()
            print("Cosmos DB client initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Cosmos DB client: {str(e)}")
            raise
    
    async def verify_containers(self) -> bool:
        """Verify that the required containers exist and are accessible."""
        print("\nVerifying Cosmos DB containers...")
        
        try:
            health_status = await self.client.health_check()
            if not health_status:
                print("Health check failed")
                return False
            
            print(f"Database: {COSMOS_CONFIG['database_name']}")
            print(f"Entities container: {ENTITIES_CONTAINER_NAME}")
            print(f"Relationships container: {RELATIONSHIPS_CONTAINER_NAME}")
            
            return True
            
        except Exception as e:
            print(f"Container verification failed: {str(e)}")
            return False
    
    async def clear_existing_data(self) -> bool:
        """Clear all existing entities and relationships."""
        print("\nClearing existing data...")
        
        try:
            for entity_type in EntityType:
                entities = await self.client.find_entities_by_type(entity_type, limit=1000)
                for entity in entities:
                    success = await self.client.delete_entity(entity.id, entity.entity_type)
                    if success:
                        print(f"  Deleted entity: {entity.id}")
                    else:
                        print(f"  Failed to delete entity: {entity.id}")
            
            print("Data clearing completed")
            return True
            
        except Exception as e:
            print(f"Data clearing failed: {str(e)}")
            return False
    
    async def load_processed_chunks(self) -> List[Dict[str, Any]]:
        """Load processed content chunks from the JSON file."""
        chunks_file = DEFAULT_VECTOR_CHUNKS_FILE
        
        if not os.path.exists(chunks_file):
            print(f"No processed chunks found at {chunks_file}")
            print("   Please run the data processing first.")
            return []
        
        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            print(f"Loaded {len(chunks)} processed chunks")
            return chunks
        except Exception as e:
            print(f"Failed to load chunks: {str(e)}")
            return []
    
    async def populate_entities(self, chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Extract and create entities from processed chunks."""
        print("\nExtracting and creating entities...")
        
        try:
            # Extract entities from chunks
            entities_by_type = extract_entities_from_chunks(chunks)
            
            # Create entities in Cosmos DB
            created_entities = {}
            total_entities = 0
            
            for entity_type, entities_dict in entities_by_type.items():
                created_entities[entity_type] = {}
                print(f"\n  Creating {len(entities_dict)} {entity_type} entities...")
                
                for entity_name, entity in entities_dict.items():
                    success = await self.client.create_entity(entity)
                    if success:
                        created_entities[entity_type][entity.id] = entity
                        total_entities += 1
                        print(f"    Created: {entity.id}")
                    else:
                        print(f"    Failed: {entity.id}")
            
            print(f"\nCreated {total_entities} entities total")
            return created_entities
            
        except Exception as e:
            print(f"Entity creation failed: {str(e)}")
            return {}
    
    async def populate_relationships(self, entities: Dict[str, Dict[str, Any]]) -> int:
        """Create relationships between entities."""
        print("\nCreating relationships...")
        
        try:
            # Generate relationships
            relationships = create_entity_relationships(entities)
            
            # Create relationships in Cosmos DB
            created_count = 0
            
            for relationship in relationships:
                success = await self.client.create_relationship(relationship)
                if success:
                    created_count += 1
                    print(f"    Created: {relationship.relationship_type.value} "
                          f"({relationship.from_entity_id} -> {relationship.to_entity_id})")
                else:
                    print(f"    Failed: {relationship.relationship_type.value} "
                          f"({relationship.from_entity_id} -> {relationship.to_entity_id})")
            
            print(f"\nCreated {created_count} relationships total")
            return created_count
            
        except Exception as e:
            print(f"Relationship creation failed: {str(e)}")
            return 0
    
    async def display_statistics(self):
        """Display database statistics."""
        print("\nDatabase Statistics:")
        
        try:
            for entity_type in EntityType:
                entities = await self.client.find_entities_by_type(entity_type, limit=1000)
                print(f"  {entity_type.value}: {len(entities)} entities")
            
            # Note: We don't have a direct way to count all relationships
            # This would require querying each relationship type
            print("  Relationships: Created successfully (see logs above)")
            
        except Exception as e:
            print(f"Failed to get statistics: {str(e)}")
    
    async def setup_database(self, clear_existing: bool = False):
        """Complete database setup process."""
        print("Starting Cosmos DB Graph Database Setup")
        print("=" * 50)
        
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
            print("No data to populate. Database setup completed with empty containers.")
            return True
        
        # Create entities
        entities = await self.populate_entities(chunks)
        if not entities:
            print("Failed to create entities")
            return False
        
        # Create relationships
        relationship_count = await self.populate_relationships(entities)
        if relationship_count == 0:
            print("No relationships created")
        
        # Display statistics
        await self.display_statistics()
        
        print("\nCosmos DB Graph Database setup completed successfully!")
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
            print("\nSetup completed successfully!")
            return 0
        else:
            print("\nSetup failed!")
            return 1
            
    except Exception as e:
        print(f"\nSetup failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 