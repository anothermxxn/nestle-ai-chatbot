# GraphRAG Integration Guide

Advanced guide for implementing and customizing the GraphRAG (Graph Retrieval-Augmented Generation) features in the Nestle AI Chatbot.

## Data Flow

1. **Content Processing**: Raw content is chunked and processed
2. **Entity Extraction**: AI identifies entities (brands, topics, products, recipes)
3. **Relationship Building**: Analyzes co-occurrence and context to create relationships
4. **Graph Storage**: Entities and relationships stored in Cosmos DB
5. **Query Enhancement**: User queries are enhanced with graph context
6. **Augmented Retrieval**: Search results are enriched with related entities
7. **Contextual Generation**: AI generates responses using graph context

## Entity Types and Models

### Supported Entity Types

```python
class EntityType(Enum):
    BRAND = "Brand"
    TOPIC = "Topic"
    PRODUCT = "Product"
    RECIPE = "Recipe"
```

#### Brand Entities
```python
{
    "id": "brand_[normalized_name]",
    "entity_type": "Brand",
    "properties": {
        "name": "BRAND_NAME",
        "category": "brand_category",
        "description": "Brand description",
        "content_types": ["recipe", "product", "brand"],
        "chunk_count": 5,
        "chunk_ids": ["chunk_1", "chunk_2", "chunk_3", ...]
    },
    "is_user_created": False,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### Product Entities
```python
{
    "id": "product_[normalized_name]",
    "entity_type": "Product", 
    "properties": {
        "name": "PRODUCT_NAME",
        "brand": "BRAND_NAME",
        "category": "product_category",
        "description": "Product description",
        "chunk_count": 5,
        "chunk_ids": ["chunk_1", "chunk_2", "chunk_3", ...]
    },
    "is_user_created": False,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### Topic Entities
```python
{
    "id": "topic_[normalized_name]",
    "entity_type": "Topic",
    "properties": {
        "name": "TOPIC_NAME",
        "category": "topic_category",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "description": "Topic description",
        "chunk_count": 5,
        "chunk_ids": ["chunk_1", "chunk_2", "chunk_3", ...]
    },
    "is_user_created": False,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### Recipe Entities
```python
{
    "id": "recipe_[normalized_title]",
    "entity_type": "Recipe",
    "properties": {
        "title": "RECIPE_TITLE",
        "recipe_type": "recipe_category",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "ingredients_mentioned": ["ingredient1", "ingredient2", "ingredient3"],
        "chunk_count": 5,
        "chunk_ids": ["chunk_1", "chunk_2", "chunk_3", ...]
    },
    "is_user_created": False,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

### Relationship Types

```python
class RelationshipType(Enum):
    BELONGS_TO = "BELONGS_TO"      # Product -> Brand
    MENTIONS = "MENTIONS"          # Topic/Product -> Brand
    CONTAINS = "CONTAINS"          # Recipe -> Product
    RELATED_TO = "RELATED_TO"      # Generic relationships
    FEATURED_IN = "FEATURED_IN"    # Brand/Product -> Topic
```

#### BELONGS_TO Relationships
```python
{
    "id": "rel_[unique_id]",
    "relationship_type": "BELONGS_TO",
    "from_entity_id": "product_[product_name]",
    "to_entity_id": "brand_[brand_name]",
    "weight": 1.0,
    "is_user_created": False,
    "properties": {
        "confidence": 0.85,
        "shared_chunks": ["chunk_1", "chunk_2", "chunk_3"]
    },
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### MENTIONS Relationships
```python
{
    "id": "rel_[unique_id]",
    "relationship_type": "MENTIONS",
    "from_entity_id": "recipe_[recipe_name]",
    "to_entity_id": "brand_[brand_name]",
    "weight": 1.0,
    "is_user_created": False,
    "properties": {
        "confidence": 0.85,
        "shared_chunks": ["chunk_1", "chunk_2", "chunk_3"]
    },
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### CONTAINS Relationships
```python
{
    "id": "rel_[unique_id]",
    "relationship_type": "CONTAINS",
    "from_entity_id": "recipe_[recipe_name]",
    "to_entity_id": "product_[product_name]",
    "weight": 1.0,
    "is_user_created": False,
    "properties": {
        "confidence": 0.85,
        "shared_chunks": ["chunk_1", "chunk_2", "chunk_3"]
    },
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### RELATED_TO Relationships
```python
{
    "id": "rel_[unique_id]",
    "relationship_type": "RELATED_TO",
    "from_entity_id": "topic_[topic_name_1]",
    "to_entity_id": "topic_[topic_name_2]",
    "weight": 1.0,
    "is_user_created": False,
    "properties": {
        "confidence": 0.85,
        "shared_chunks": ["chunk_1", "chunk_2", "chunk_3"]
    },
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

#### FEATURED_IN Relationships
```python
{
    "id": "rel_[unique_id]",
    "relationship_type": "FEATURED_IN",
    "from_entity_id": "brand_[brand_name]",
    "to_entity_id": "topic_[topic_name]",
    "weight": 1.0,
    "is_user_created": False,
    "properties": {
        "confidence": 0.85,
        "shared_chunks": ["chunk_1", "chunk_2", "chunk_3"]
    },
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00"
}
```

## Customization

### Custom Entity Types

To add new types:

```python
class EntityType(Enum):
    BRAND = "Brand"
    TOPIC = "Topic"
    PRODUCT = "Product"
    RECIPE = "Recipe"
    # Add new entity types here
    INGREDIENT = "Ingredient"
    TECHNIQUE = "Technique"
```

### Custom Relationship Types

To add new relationship types:

```python
class RelationshipType(Enum):
    BELONGS_TO = "BELONGS_TO"
    MENTIONS = "MENTIONS"
    CONTAINS = "CONTAINS"
    RELATED_TO = "RELATED_TO"
    FEATURED_IN = "FEATURED_IN"
    # Add new relationship types here
    INGREDIENT_OF = "INGREDIENT_OF"
    TECHNIQUE_FOR = "TECHNIQUE_FOR"
```

### Create User-Defined Entity

**POST** `/api/graph/entities`

**Required Fields:**
- `entity_type`: "Brand", "Topic", "Product", or "Recipe"
- `properties`: Object with entity-specific properties

**Entity Property Requirements:**
- **Brand**: `name`
- **Topic**: `name`, `category`  
- **Product**: `name`
- **Recipe**: `title`

**Example Request:**
```json
{
  "entity_type": "Brand",
  "properties": {
    "name": "My Custom Brand",
    "category": "custom_category",
    "description": "Brand description"
  }
}
```

### Create User-Defined Relationship

**POST** `/api/graph/relationships`

**Required Fields:**
- `from_entity_id`: Source entity ID
- `to_entity_id`: Target entity ID
- `relationship_type`: "BELONGS_TO", "MENTIONS", "CONTAINS", "RELATED_TO", or "FEATURED_IN"

**Optional Fields:**
- `properties`: Object with custom properties
- `weight`: Number between 0.0 and 1.0 (default: 1.0)

**Example Request:**
```json
{
  "from_entity_id": "user_product_custom_item_xyz789",
  "to_entity_id": "user_brand_my_custom_brand_abc123",
  "relationship_type": "BELONGS_TO",
  "properties": {
    "confidence": 0.95
  },
  "weight": 1.0
}
```

This API allows users to dynamically extend the knowledge graph with their own entities and relationships, enabling customization for specific use cases and domains.