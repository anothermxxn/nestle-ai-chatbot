import asyncio
import sys
import os
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "src"))
from graph.cosmos_client import CosmosGraphClient
from graph.models import EntityType

async def get_user_created_entities(client: CosmosGraphClient) -> List:
    """
    Get all user-created entities from the database.
    
    Args:
        client: Graph client instance
        
    Returns:
        List: List of user-created entities
    """
    user_entities = []
    
    for entity_type in EntityType:
        print(f"Checking {entity_type.value} entities...")
        
        entities = await client.find_entities_by_type(entity_type, limit=1000)
        
        for entity in entities:
            if entity.is_user_created:
                user_entities.append(entity)
                print(f"  Found user-created {entity_type.value}: {entity.id}")
    
    return user_entities


async def get_relationships_for_entities(client: CosmosGraphClient, entity_ids: List[str]) -> List:
    """
    Get all relationships connected to the given entities.
    
    Args:
        client: Graph client instance
        entity_ids: List of entity IDs
        
    Returns:
        List: List of relationships
    """
    relationships = []
    
    for entity_id in entity_ids:
        print(f"Checking relationships for entity: {entity_id}")
        
        entity_relationships = await client.get_entity_relationships(entity_id, "both")
        
        for rel in entity_relationships:
            if rel not in relationships:
                relationships.append(rel)
                print(f"  Found relationship: {rel.id} ({rel.relationship_type.value})")
    
    return relationships


async def cleanup_user_data():
    """Main cleanup function."""
    print("🧹 Starting cleanup of user-created test data...")
    print("=" * 50)
    
    try:
        client = CosmosGraphClient()
        
        # Get all user-created entities
        print("\nFinding user-created entities...")
        user_entities = await get_user_created_entities(client)
        
        if not user_entities:
            print("✅ No user-created entities found. Database is already clean!")
            return
        
        print(f"\nFound {len(user_entities)} user-created entities")
        
        entity_ids = [entity.id for entity in user_entities]
        
        # Find related relationships
        print("\nFinding related relationships...")
        relationships = await get_relationships_for_entities(client, entity_ids)
        
        print(f"\nFound {len(relationships)} related relationships")
        
        print("\n⚠️  About to delete:")
        print(f"   - {len(user_entities)} user-created entities")
        print(f"   - {len(relationships)} related relationships")
        
        confirmation = input("\nAre you sure you want to delete all this data? (yes/no): ")
        
        if confirmation.lower() not in ["yes", "y"]:
            print("❌ Cleanup cancelled.")
            return
        
        # Delete relationships
        print(f"\nDeleting {len(relationships)} relationships...")
        deleted_relationships = 0
        
        for rel in relationships:
            try:
                success = await client.delete_relationship(rel.id)
                if success:
                    deleted_relationships += 1
                    print(f"  ✅ Deleted relationship: {rel.id}")
                else:
                    print(f"  ❌ Failed to delete relationship: {rel.id}")
            except Exception as e:
                print(f"  ❌ Error deleting relationship {rel.id}: {e}")
        
        # Delete entities
        print(f"\nDeleting {len(user_entities)} entities...")
        deleted_entities = 0
        
        for entity in user_entities:
            try:
                success = await client.delete_entity(entity.id, entity.entity_type)
                if success:
                    deleted_entities += 1
                    print(f"  ✅ Deleted entity: {entity.id} ({entity.entity_type.value})")
                else:
                    print(f"  ❌ Failed to delete entity: {entity.id}")
            except Exception as e:
                print(f"  ❌ Error deleting entity {entity.id}: {e}")
        
        print("\n" + "=" * 50)
        print("Cleanup completed!")
        print(f"   ✅ Deleted {deleted_entities}/{len(user_entities)} entities")
        print(f"   ✅ Deleted {deleted_relationships}/{len(relationships)} relationships")
        
        if deleted_entities < len(user_entities) or deleted_relationships < len(relationships):
            print("   ⚠️ Some items could not be deleted. Check the logs above.")
        else:
            print("   All user-created test data has been successfully removed!")
            
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        print("   Please check your database connection and try again.")


async def list_user_data():
    """List user-created data without deleting."""
    print("Listing user-created test data...")
    print("=" * 50)
    
    try:
        client = CosmosGraphClient()
        
        user_entities = await get_user_created_entities(client)
        
        if not user_entities:
            print("✅ No user-created entities found.")
            return
        
        print(f"\nFound {len(user_entities)} user-created entities:")
        
        # Group by type
        by_type = {}
        for entity in user_entities:
            entity_type = entity.entity_type.value
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        for entity_type, entities in by_type.items():
            print(f"\n  {entity_type} ({len(entities)} entities):")
            for entity in entities:
                name = entity.properties.get("name") or entity.properties.get("title", "Unknown")
                print(f"    - {entity.id}: {name}")
        
        # Get relationships
        entity_ids = [entity.id for entity in user_entities]
        relationships = await get_relationships_for_entities(client, entity_ids)
        
        print(f"\nFound {len(relationships)} related relationships")
        
    except Exception as e:
        print(f"❌ Error listing data: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        asyncio.run(list_user_data())
    else:
        asyncio.run(cleanup_user_data())


if __name__ == "__main__":
    main() 