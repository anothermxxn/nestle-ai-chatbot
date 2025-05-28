#!/usr/bin/env python3
import asyncio
import sys
import os
from typing import List

backend_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
backend_src_path = os.path.join(backend_root, "src")
sys.path.insert(0, os.path.abspath(backend_root))
sys.path.insert(0, os.path.abspath(backend_src_path))
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


async def get_user_created_relationships(client: CosmosGraphClient) -> List:
    """
    Get all user-created relationships from the database.
    
    Args:
        client: Graph client instance
        
    Returns:
        List: List of user-created relationships
    """
    print("Checking user-created relationships...")
    user_relationships = []
    
    # Get all relationships and filter for user-created ones
    all_relationships = await client.get_all_relationships(limit=10000)
    
    for rel in all_relationships:
        if rel.is_user_created:
            user_relationships.append(rel)
            print(f"  Found user-created relationship: {rel.id} ({rel.relationship_type.value})")
    
    return user_relationships


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
        
        # Get all user-created relationships
        print("\nFinding user-created relationships...")
        user_relationships = await get_user_created_relationships(client)
        
        # Get relationships connected to user-created entities (may include system relationships)
        if user_entities:
            entity_ids = [entity.id for entity in user_entities]
            print("\nFinding relationships connected to user-created entities...")
            connected_relationships = await get_relationships_for_entities(client, entity_ids)
        else:
            connected_relationships = []
        
        # Combine all relationships to delete (avoid duplicates)
        all_relationships_to_delete = []
        relationship_ids_seen = set()
        
        # Add user-created relationships
        for rel in user_relationships:
            if rel.id not in relationship_ids_seen:
                all_relationships_to_delete.append(rel)
                relationship_ids_seen.add(rel.id)
        
        # Add relationships connected to user entities
        for rel in connected_relationships:
            if rel.id not in relationship_ids_seen:
                all_relationships_to_delete.append(rel)
                relationship_ids_seen.add(rel.id)
        
        # Check if anything to clean up
        if not user_entities and not all_relationships_to_delete:
            print("✅ No user-created data found. Database is already clean!")
            return
        
        print(f"\nFound {len(user_entities)} user-created entities")
        print(f"Found {len(user_relationships)} user-created relationships")
        print(f"Found {len(connected_relationships)} relationships connected to user entities")
        print(f"Total relationships to delete: {len(all_relationships_to_delete)}")
        
        print("\n⚠️  About to delete:")
        print(f"   - {len(user_entities)} user-created entities")
        print(f"   - {len(all_relationships_to_delete)} relationships (user-created + connected)")
        
        confirmation = input("\nAre you sure you want to delete all this data? (yes/no): ")
        
        if confirmation.lower() not in ["yes", "y"]:
            print("❌ Cleanup cancelled.")
            return
        
        # Delete relationships
        print(f"\nDeleting {len(all_relationships_to_delete)} relationships...")
        deleted_relationships = 0
        
        for rel in all_relationships_to_delete:
            try:
                success = await client.delete_relationship(rel.id)
                if success:
                    deleted_relationships += 1
                    user_flag = "👤" if rel.is_user_created else "🤖"
                    print(f"  ✅ Deleted relationship: {rel.id} {user_flag}")
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
        print(f"   ✅ Deleted {deleted_relationships}/{len(all_relationships_to_delete)} relationships")
        
        if deleted_entities < len(user_entities) or deleted_relationships < len(all_relationships_to_delete):
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
        user_relationships = await get_user_created_relationships(client)
        
        if not user_entities and not user_relationships:
            print("✅ No user-created data found.")
            return
        
        # Display entities
        if user_entities:
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
        else:
            print("\n✅ No user-created entities found.")
        
        # Display relationships
        if user_relationships:
            print(f"\nFound {len(user_relationships)} user-created relationships:")
            
            # Group by type
            by_rel_type = {}
            for rel in user_relationships:
                rel_type = rel.relationship_type.value
                if rel_type not in by_rel_type:
                    by_rel_type[rel_type] = []
                by_rel_type[rel_type].append(rel)
            
            for rel_type, relationships in by_rel_type.items():
                print(f"\n  {rel_type} ({len(relationships)} relationships):")
                for rel in relationships:
                    print(f"    - {rel.id}: {rel.from_entity_id} → {rel.to_entity_id}")
        else:
            print("\n✅ No user-created relationships found.")
        
        # Show summary
        if user_entities or user_relationships:
            print(f"\n📊 Summary:")
            print(f"   - Total user-created entities: {len(user_entities)}")
            print(f"   - Total user-created relationships: {len(user_relationships)}")
        
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