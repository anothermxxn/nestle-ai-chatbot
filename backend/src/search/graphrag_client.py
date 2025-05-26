import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from utils.import_helper import setup_imports
setup_imports(__file__)
from search.search_client import AzureSearchClient
from graph.cosmos_client import CosmosGraphClient
from graph.models import EntityType, Entity, Relationship

logger = logging.getLogger(__name__)

@dataclass
class GraphRAGResult:
    """Enhanced search result that includes graph context."""
    vector_results: List[Dict]
    related_entities: List[Entity]
    contextual_relationships: List[Relationship]
    combined_score: float
    retrieval_metadata: Dict[str, Any]

class GraphRAGClient:
    """
    Unified client that combines vector search with graph traversal for enhanced RAG.
    """
    
    def __init__(self):
        """Initialize the GraphRAG client with vector and graph clients."""
        try:
            self.vector_client = AzureSearchClient(enable_enhanced_ranking=True)
            self.graph_client = CosmosGraphClient()
            
            self.config = {
                "vector_weight": 0.7,
                "graph_weight": 0.3,
                "max_graph_depth": 2,
                "min_relationship_weight": 0.1,
                "entity_boost_factor": 1.2,
                "relationship_boost_factor": 1.1
            }
            
            logger.info("GraphRAG client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GraphRAG client: {str(e)}")
            raise
    
    async def hybrid_search(
        self,
        query: str,
        content_type: Optional[str] = None,
        brand: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        top_results: int = 10,
        graph_expansion_depth: int = 1
    ) -> GraphRAGResult:
        """
        Perform hybrid search combining vector search with graph traversal.
        
        Args:
            query (str): Search query
            content_type (Optional[str]): Filter by content type
            brand (Optional[str]): Filter by brand
            keywords (Optional[List[str]]): Filter by keywords
            top_results (int): Number of top results to return
            graph_expansion_depth (int): Depth of graph traversal for expansion
            
        Returns:
            GraphRAGResult: Combined search results with graph context
        """
        try:
            logger.info(f"Starting hybrid search for query: {query}")
            
            # Perform vector search
            vector_results = await self._perform_vector_search(
                query, content_type, brand, keywords, top_results * 2
            )
            
            # Extract entities from query and results
            query_entities = await self._extract_entities_from_query(query)
            result_entities = await self._extract_entities_from_results(vector_results)
            
            # Perform graph traversal
            graph_context = []
            contextual_relationships = []
            graph_context, contextual_relationships = await self._expand_with_graph_traversal(
                query_entities + result_entities,
                depth=graph_expansion_depth
            )
            
            # Combine and rank results
            enhanced_results = await self._combine_and_rank_results(
                vector_results,
                query_entities + result_entities + graph_context,
                contextual_relationships,
                query
            )
            
            final_results = enhanced_results[:top_results]
            retrieval_metadata = {
                "vector_results_count": len(vector_results),
                "graph_entities_found": len(query_entities + result_entities),
                "graph_expansion_entities": len(graph_context),
                "relationships_found": len(contextual_relationships),
                "final_results_count": len(final_results),
                "expansion_depth": graph_expansion_depth
            }
            
            logger.info(f"Hybrid search completed: {retrieval_metadata}")
            
            return GraphRAGResult(
                vector_results=final_results,
                related_entities=query_entities + result_entities + graph_context,
                contextual_relationships=contextual_relationships,
                combined_score=self._calculate_overall_relevance(final_results),
                retrieval_metadata=retrieval_metadata
            )
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            # Fallback to vector search only
            vector_results = await self._perform_vector_search(
                query, content_type, brand, keywords, top_results
            )
            
            return GraphRAGResult(
                vector_results=vector_results,
                related_entities=[],
                contextual_relationships=[],
                combined_score=0.5,
                retrieval_metadata={
                    "error": str(e),
                    "fallback_to_vector_only": True,
                    "vector_results_count": len(vector_results)
                }
            )
    
    async def _perform_vector_search(
        self,
        query: str,
        content_type: Optional[str],
        brand: Optional[str],
        keywords: Optional[List[str]],
        top_results: int
    ) -> List[Dict]:
        """Perform vector search using the existing search client."""
        try:
            return await self.vector_client.search(
                query=query,
                text_query=query,
                content_type=content_type,
                brand=brand,
                keywords=keywords,
                top=top_results,
                enable_ranking=True
            )
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []
    
    async def _extract_entities_from_query(self, query: str) -> List[Entity]:
        """Extract entities that might be relevant to the query."""
        try:
            entities = []
            query_lower = query.lower()
            
            # Search for brand entities
            for entity_type in EntityType:
                type_entities = await self.graph_client.find_entities_by_type(entity_type, limit=100)
                
                for entity in type_entities:
                    entity_name = entity.properties.get("name", "").lower()
                    if entity_name and entity_name in query_lower:
                        entities.append(entity)
                        logger.info(f"Found query entity: {entity.id} ({entity_type.value})")
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract entities from query: {str(e)}")
            return []
    
    async def _extract_entities_from_results(self, results: List[Dict]) -> List[Entity]:
        """Extract entities related to the search results."""
        try:
            entities = []
            
            # Extract chunk IDs from results
            chunk_ids = []
            for result in results:
                chunk_id = f"{result.get('url', '')}_{result.get('doc_index', 0)}_{result.get('chunk_index', 0)}"
                chunk_ids.append(chunk_id)
            
            # Find entities that reference these chunks
            for entity_type in EntityType:
                type_entities = await self.graph_client.find_entities_by_type(entity_type, limit=200)
                
                for entity in type_entities:
                    entity_chunk_ids = entity.properties.get("chunk_ids", [])
                    if any(chunk_id in entity_chunk_ids for chunk_id in chunk_ids):
                        entities.append(entity)
                        logger.info(f"Found result entity: {entity.id} ({entity_type.value})")
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to extract entities from results: {str(e)}")
            return []
    
    async def _expand_with_graph_traversal(
        self,
        seed_entities: List[Entity],
        depth: int = 1
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Expand context using graph traversal from seed entities."""
        try:
            expanded_entities = []
            all_relationships = []
            
            current_entities = seed_entities.copy()
            remaining_depth = depth
            
            while remaining_depth > 0 and current_entities:
                next_level_entities = []
                
                for entity in current_entities:
                    relationships = await self.graph_client.get_entity_relationships(
                        entity.id, direction="both"
                    )
                    
                    for rel in relationships:
                        if rel.weight >= self.config["min_relationship_weight"]:
                            all_relationships.append(rel)
                            
                            connected_entity_id = (
                                rel.to_entity_id if rel.from_entity_id == entity.id 
                                else rel.from_entity_id
                            )
                            
                            for entity_type in EntityType:
                                connected_entities = await self.graph_client.find_entities_by_type(
                                    entity_type, limit=1000
                                )
                                
                                for connected_entity in connected_entities:
                                    if connected_entity.id == connected_entity_id:
                                        if connected_entity not in expanded_entities:
                                            expanded_entities.append(connected_entity)
                                            next_level_entities.append(connected_entity)
                                        break
                
                current_entities = next_level_entities
                remaining_depth -= 1
            
            logger.info(f"Graph traversal found {len(expanded_entities)} entities and {len(all_relationships)} relationships")
            return expanded_entities, all_relationships
            
        except Exception as e:
            logger.error(f"Graph traversal failed: {str(e)}")
            return [], []
    
    async def _combine_and_rank_results(
        self,
        vector_results: List[Dict],
        entities: List[Entity],
        relationships: List[Relationship],
        query: str
    ) -> List[Dict]:
        """Combine vector results with graph context and re-rank."""
        try:
            enhanced_results = []
            query_lower = query.lower()
            
            for result in vector_results:
                enhanced_result = result.copy()
                
                # Get base vector score
                vector_score = result.get("relevance_score", result.get("@search.score", 0.0))
                if isinstance(vector_score, str):
                    vector_score = float(vector_score)
                
                # Calculate graph relevance score
                graph_score = self._calculate_graph_relevance(result, entities, relationships)
                
                # Calculate query-specific boost
                query_boost = self._calculate_query_relevance_boost(result, entities, query_lower)
                
                # Combine scores with query boost
                combined_score = (
                    vector_score * self.config["vector_weight"] +
                    graph_score * self.config["graph_weight"] +
                    query_boost * 0.1
                )
                
                # Add graph context to result
                enhanced_result["graph_enhanced_score"] = combined_score
                enhanced_result["original_vector_score"] = vector_score
                enhanced_result["graph_relevance_score"] = graph_score
                enhanced_result["query_relevance_boost"] = query_boost
                enhanced_result["graph_context"] = self._get_result_graph_context(
                    result, entities, relationships
                )
                
                enhanced_results.append(enhanced_result)
            
            # Sort by combined score
            enhanced_results.sort(key=lambda x: x["graph_enhanced_score"], reverse=True)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Failed to combine and rank results: {str(e)}")
            return vector_results
    
    def _calculate_graph_relevance(
        self,
        result: Dict,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> float:
        """Calculate graph-based relevance score for a result."""
        try:
            score = 0.0
            
            # Create chunk ID for this result
            result_chunk_id = f"{result.get('url', '')}_{result.get('doc_index', 0)}_{result.get('chunk_index', 0)}"
            
            # Score based on entity connections
            for entity in entities:
                entity_chunk_ids = entity.properties.get("chunk_ids", [])
                if result_chunk_id in entity_chunk_ids:
                    score += 0.5 * self.config["entity_boost_factor"]
            
            # Score based on relationship connections
            for relationship in relationships:
                # Check if this result is connected through relationships
                if relationship.weight > self.config["min_relationship_weight"]:
                    score += 0.3 * relationship.weight * self.config["relationship_boost_factor"]
            
            # Normalize score to 0-1 range
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate graph relevance: {str(e)}")
            return 0.0
    
    def _calculate_query_relevance_boost(
        self,
        result: Dict,
        entities: List[Entity],
        query_lower: str
    ) -> float:
        """Calculate query-specific relevance boost based on entity names and content."""
        try:
            boost = 0.0
            result_chunk_id = f"{result.get('url', '')}_{result.get('doc_index', 0)}_{result.get('chunk_index', 0)}"
            
            # Boost for entities whose names appear in the query
            for entity in entities:
                entity_chunk_ids = entity.properties.get("chunk_ids", [])
                if result_chunk_id in entity_chunk_ids:
                    entity_name = entity.properties.get("name", "").lower()
                    if entity_name and entity_name in query_lower:
                        # Higher boost for exact entity name matches
                        boost += 0.5
                    elif entity_name:
                        # Partial boost for entity name word matches
                        entity_words = entity_name.split()
                        query_words = query_lower.split()
                        word_matches = sum(1 for word in entity_words if word in query_words)
                        if word_matches > 0:
                            boost += 0.2 * (word_matches / len(entity_words))
            
            # Boost for content that contains query terms
            content = result.get("content", "").lower()
            if content and query_lower in content:
                boost += 0.3
            
            # Boost for title matches
            title = result.get("page_title", "").lower()
            if title and query_lower in title:
                boost += 0.4
            
            # Normalize boost to 0-1 range
            return min(boost, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate query relevance boost: {str(e)}")
            return 0.0
    
    def _get_result_graph_context(
        self,
        result: Dict,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """Get graph context information for a result."""
        try:
            result_chunk_id = f"{result.get('url', '')}_{result.get('doc_index', 0)}_{result.get('chunk_index', 0)}"
            
            related_entities = []
            related_relationships = []
            
            # Find entities related to this result
            for entity in entities:
                entity_chunk_ids = entity.properties.get("chunk_ids", [])
                if result_chunk_id in entity_chunk_ids:
                    related_entities.append({
                        "id": entity.id,
                        "type": entity.entity_type.value,
                        "name": entity.properties.get("name", ""),
                        "properties": entity.properties
                    })
            
            # Find relationships involving these entities
            entity_ids = [e["id"] for e in related_entities]
            for relationship in relationships:
                if (relationship.from_entity_id in entity_ids or 
                    relationship.to_entity_id in entity_ids):
                    related_relationships.append({
                        "type": relationship.relationship_type.value,
                        "from": relationship.from_entity_id,
                        "to": relationship.to_entity_id,
                        "weight": relationship.weight,
                        "properties": relationship.properties
                    })
            
            return {
                "related_entities": related_entities,
                "related_relationships": related_relationships,
                "entity_count": len(related_entities),
                "relationship_count": len(related_relationships)
            }
            
        except Exception as e:
            logger.error(f"Failed to get graph context: {str(e)}")
            return {"related_entities": [], "related_relationships": []}
    
    def _calculate_overall_relevance(self, results: List[Dict]) -> float:
        """Calculate overall relevance score for the result set."""
        if not results:
            return 0.0
        
        scores = [r.get("graph_enhanced_score", 0.0) for r in results]
        return sum(scores) / len(scores)
    
    async def get_entity_context(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get detailed context for a specific entity with configurable traversal depth."""
        try:
            # Get the root entity
            root_entity = None
            for entity_type in EntityType:
                entities = await self.graph_client.find_entities_by_type(entity_type, limit=1000)
                for e in entities:
                    if e.id == entity_id:
                        root_entity = e
                        break
                if root_entity:
                    break
            
            if not root_entity:
                return {"error": f"Entity {entity_id} not found"}
            
            # Perform depth-based traversal to get all connected entities and relationships
            all_entities = [root_entity]
            all_relationships = []
            visited_entity_ids = {entity_id}
            current_entities = [root_entity]
            remaining_depth = depth
            
            while remaining_depth > 0 and current_entities:
                next_level_entities = []
                
                for entity in current_entities:
                    relationships = await self.graph_client.get_entity_relationships(entity.id, "both")
                    
                    for rel in relationships:
                        if rel not in all_relationships:
                            all_relationships.append(rel)
                        
                        connected_entity_id = (
                            rel.to_entity_id if rel.from_entity_id == entity.id 
                            else rel.from_entity_id
                        )
                        
                        if connected_entity_id in visited_entity_ids:
                            continue
                        
                        for entity_type in EntityType:
                            type_entities = await self.graph_client.find_entities_by_type(entity_type, limit=1000)
                            for connected_entity in type_entities:
                                if connected_entity.id == connected_entity_id:
                                    all_entities.append(connected_entity)
                                    next_level_entities.append(connected_entity)
                                    visited_entity_ids.add(connected_entity_id)
                                    break
                
                current_entities = next_level_entities
                remaining_depth -= 1
            
            # Separate connected entities (exclude root entity)
            connected_entities = [e for e in all_entities if e.id != entity_id]
            
            return {
                "entity": {
                    "id": root_entity.id,
                    "type": root_entity.entity_type.value,
                    "properties": root_entity.properties
                },
                "relationships": [
                    {
                        "type": rel.relationship_type.value,
                        "from": rel.from_entity_id,
                        "to": rel.to_entity_id,
                        "weight": rel.weight,
                        "properties": rel.properties
                    }
                    for rel in all_relationships
                ],
                "connected_entities": [
                    {
                        "id": e.id,
                        "type": e.entity_type.value,
                        "properties": e.properties
                    }
                    for e in connected_entities
                ],
                "traversal_metadata": {
                    "requested_depth": depth,
                    "total_entities_found": len(all_entities),
                    "total_relationships_found": len(all_relationships),
                    "connected_entities_count": len(connected_entities)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get entity context: {str(e)}")
            return {"error": str(e)} 