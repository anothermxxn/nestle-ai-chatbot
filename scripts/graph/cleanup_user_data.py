#!/usr/bin/env python3
import asyncio
import logging
import sys
import os
from typing import List

backend_root = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
backend_src_path = os.path.join(backend_root, "src")
sys.path.insert(0, os.path.abspath(backend_root))
sys.path.insert(0, os.path.abspath(backend_src_path))
from graph.services.cosmos_service import CosmosGraphClient
from graph.models.entity import EntityType

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

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
        entities = await client.find_entities_by_type(entity_type, limit=1000)
        
        for entity in entities:
            if entity.is_user_created:
                user_entities.append(entity)
                logger.info(f"  Found user-created {entity_type.value}: {entity.id}")
    
    return user_entities


async def get_user_created_relationships(client: CosmosGraphClient) -> List:
    """
    Get all user-created relationships from the database.
    
    Args:
        client: Graph client instance
        
    Returns:
        List: List of user-created relationships
    """
    user_relationships = []
    
    # Get all relationships and filter for user-created ones
    all_relationships = await client.get_all_relationships(limit=10000)
    
    for rel in all_relationships:
        if rel.is_user_created:
            user_relationships.append(rel)
            logger.info(f"  Found user-created relationship: {rel.id} ({rel.relationship_type.value})")
    
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
        entity_relationships = await client.get_entity_relationships(entity_id, "both")
        
        for rel in entity_relationships:
            if rel not in relationships:
                relationships.append(rel)
                logger.info(f"  Found relationship: {rel.id} ({rel.relationship_type.value})")
    
    return relationships


async def cleanup_user_data():
    """Main cleanup function."""
    logger.info("🧹 Starting cleanup of user-created test data...")
    logger.info("=" * 50)
    
    try:
        client = CosmosGraphClient()
        
        # Get all user-created entities
        logger.info("\nFinding user-created entities...")
        user_entities = await get_user_created_entities(client)
        
        # Get all user-created relationships
        logger.info("\nFinding user-created relationships...")
        user_relationships = await get_user_created_relationships(client)
        
        # Get relationships connected to user-created entities (may include system relationships)
        if user_entities:
            entity_ids = [entity.id for entity in user_entities]
            logger.info("\nFinding relationships connected to user-created entities...")
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
            logger.info("✅ No user-created data found. Database is already clean!")
            return
        
        print("\n⚠️  About to delete:")
        print(f"   - {len(user_entities)} user-created entities")
        print(f"   - {len(all_relationships_to_delete)} relationships (user-created + connected)")
        
        confirmation = input("\nAre you sure you want to delete all this data? (yes/no): ")
        
        if confirmation.lower() not in ["yes", "y"]:
            logger.warning("❌ Cleanup cancelled.")
            return
        
        # Delete relationships
        logger.info(f"\nDeleting {len(all_relationships_to_delete)} relationships...")
        deleted_relationships = 0
        
        for rel in all_relationships_to_delete:
            try:
                success = await client.delete_relationship(rel.id)
                if success:
                    deleted_relationships += 1
                    user_flag = "👤" if rel.is_user_created else "🤖"
                else:
                    logger.warning(f"  ❌ Failed to delete relationship: {rel.id}")
            except Exception as e:
                logger.error(f"  ❌ Error deleting relationship {rel.id}: {e}")
        
        # Delete entities
        logger.info(f"\nDeleting {len(user_entities)} entities...")
        deleted_entities = 0
        
        for entity in user_entities:
            try:
                success = await client.delete_entity(entity.id, entity.entity_type)
                if success:
                    deleted_entities += 1
                else:
                    logger.warning(f"  ❌ Failed to delete entity: {entity.id}")
            except Exception as e:
                logger.error(f"  ❌ Error deleting entity {entity.id}: {e}")
        
        logger.info("\n" + "=" * 50)
        logger.info("Cleanup completed!")
        logger.info(f"   ✅ Deleted {deleted_entities}/{len(user_entities)} entities")
        logger.info(f"   ✅ Deleted {deleted_relationships}/{len(all_relationships_to_delete)} relationships")
        
        if deleted_entities < len(user_entities) or deleted_relationships < len(all_relationships_to_delete):
            logger.warning("   ⚠️ Some items could not be deleted.")
        else:
            logger.info("   All user-created test data has been successfully removed!")
            
    except Exception as e:
        logger.error(f"\n❌ Error during cleanup: {e}")

async def list_user_data():
    """List user-created data without deleting."""
    logger.info("Listing user-created test data...")
    logger.info("=" * 50)
    
    try:
        client = CosmosGraphClient()
        
        # Get all user-created entities
        user_entities = await get_user_created_entities(client)
        
        # Get all user-created relationships
        user_relationships = await get_user_created_relationships(client)
        
        if not user_entities and not user_relationships:
            logger.info("✅ No user-created data found.")
            return
        
        if user_entities:
            # Group entities by type for better display
            entities_by_type = {}
            for entity in user_entities:
                entity_type = entity.entity_type.value
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)
            
            logger.info(f"\nFound {len(user_entities)} user-created entities:")
            for entity_type, entities in entities_by_type.items():
                logger.info(f"\n  {entity_type} ({len(entities)} entities):")
                for entity in entities:
                    name = getattr(entity, 'name', entity.id)
                    logger.info(f"    - {entity.id}: {name}")
        else:
            logger.info("\n✅ No user-created entities found.")
        
        if user_relationships:
            # Group relationships by type for better display
            relationships_by_type = {}
            for rel in user_relationships:
                rel_type = rel.relationship_type.value
                if rel_type not in relationships_by_type:
                    relationships_by_type[rel_type] = []
                relationships_by_type[rel_type].append(rel)
            
            logger.info(f"\nFound {len(user_relationships)} user-created relationships:")
            for rel_type, relationships in relationships_by_type.items():
                logger.info(f"\n  {rel_type} ({len(relationships)} relationships):")
                for rel in relationships:
                    logger.info(f"    - {rel.id}: {rel.from_entity_id} → {rel.to_entity_id}")
        else:
            logger.info("\n✅ No user-created relationships found.")
        
        # Summary
        logger.info(f"\nSummary:")
        logger.info(f"   - Total user-created entities: {len(user_entities)}")
        logger.info(f"   - Total user-created relationships: {len(user_relationships)}")
        
    except Exception as e:
        logger.error(f"❌ Error listing data: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup or list user-created test data in Cosmos DB")
    parser.add_argument("--list", action="store_true", help="List user-created data without deleting")
    
    args = parser.parse_args()
    
    if args.list:
        asyncio.run(list_user_data())
    else:
        asyncio.run(cleanup_user_data())


if __name__ == "__main__":
    main() 