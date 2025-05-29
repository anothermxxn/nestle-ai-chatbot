import logging
from typing import Dict, List, Any
from dataclasses import dataclass

try:
    from backend.src.search.graphrag_client import GraphRAGResult
    from backend.src.graph.models import Entity, Relationship
except ImportError:
    from src.search.graphrag_client import GraphRAGResult
    from src.graph.models import Entity, Relationship

logger = logging.getLogger(__name__)

@dataclass
class GraphContext:
    """Structured graph context for LLM prompts."""
    entities_summary: str
    relationships_summary: str
    enhanced_sources: str
    metadata: Dict[str, Any]

class GraphRAGFormatter:
    """
    Formatter that converts GraphRAG results into enhanced context for LLM responses.
    """
    
    def __init__(self):
        """Initialize the GraphRAG formatter."""
        self.entity_type_descriptions = {
            "Brand": "brand or company",
            "Product": "product or item",
            "Recipe": "recipe or cooking instruction",
            "Topic": "topic or theme"
        }
        
        self.relationship_descriptions = {
            "BELONGS_TO": "belongs to",
            "MENTIONS": "mentions or references",
            "CONTAINS": "contains or includes",
            "RELATED_TO": "is related to",
            "FEATURED_IN": "is featured in"
        }
    
    def format_graphrag_context(self, graphrag_result: GraphRAGResult, query: str) -> GraphContext:
        """
        Format GraphRAG results into structured context for LLM.
        
        Args:
            graphrag_result (GraphRAGResult): Results from GraphRAG search
            query (str): Original user query
            
        Returns:
            GraphContext: Formatted context for LLM
        """
        try:
            entities_summary = self._format_entities_summary(graphrag_result.related_entities)
            relationships_summary = self._format_relationships_summary(
                graphrag_result.contextual_relationships
            )
            
            enhanced_sources = self._format_enhanced_sources(graphrag_result.vector_results)
            
            metadata = {
                "total_entities": len(graphrag_result.related_entities),
                "total_relationships": len(graphrag_result.contextual_relationships),
                "combined_score": graphrag_result.combined_score,
                "retrieval_metadata": graphrag_result.retrieval_metadata
            }
            
            return GraphContext(
                entities_summary=entities_summary,
                relationships_summary=relationships_summary,
                enhanced_sources=enhanced_sources,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to format GraphRAG context: {str(e)}")
            return GraphContext(
                entities_summary="",
                relationships_summary="",
                enhanced_sources=self._format_basic_sources(graphrag_result.vector_results),
                metadata={"error": str(e)}
            )
    
    def _format_entities_summary(self, entities: List[Entity]) -> str:
        """Format entities into a readable summary."""
        if not entities:
            return ""
        
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.entity_type.value
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        summary_parts = []
        for entity_type, type_entities in entities_by_type.items():
            type_desc = self.entity_type_descriptions.get(entity_type, entity_type.lower())
            entity_names = []
            
            for entity in type_entities:
                name = entity.properties.get("name", entity.id)
                entity_names.append(name)
            
            if entity_names:
                if len(entity_names) == 1:
                    summary_parts.append(f"The {type_desc} '{entity_names[0]}'")
                else:
                    names_str = "', '".join(entity_names[:-1]) + f"', and '{entity_names[-1]}'"
                    summary_parts.append(f"The {type_desc}s '{names_str}'")
        
        if summary_parts:
            return "Related entities: " + "; ".join(summary_parts) + "."
        return ""
    
    def _format_relationships_summary(self, relationships: List[Relationship]) -> str:
        """Format relationships into a readable summary."""
        if not relationships:
            return ""
        
        relationships_by_type = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value
            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []
            relationships_by_type[rel_type].append(rel)
        
        summary_parts = []
        for rel_type, type_relationships in relationships_by_type.items():
            rel_desc = self.relationship_descriptions.get(rel_type, rel_type.lower().replace("_", " "))
            
            rel_descriptions = []
            for rel in type_relationships[:3]:
                from_name = self._get_entity_name_from_id(rel.from_entity_id)
                to_name = self._get_entity_name_from_id(rel.to_entity_id)
                rel_descriptions.append(f"{from_name} {rel_desc} {to_name}")
            
            if rel_descriptions:
                summary_parts.extend(rel_descriptions)
                if len(type_relationships) > 3:
                    summary_parts.append(f"and {len(type_relationships) - 3} more {rel_type.lower()} relationships")
        
        if summary_parts:
            return "Key relationships: " + "; ".join(summary_parts) + "."
        return ""
    
    def _format_enhanced_sources(self, results: List[Dict]) -> str:
        """Format search results with graph context enhancement."""
        if not results:
            return "No relevant sources found."
        
        formatted_sources = []
        
        for i, result in enumerate(results, 1):
            # Basic source information
            source_parts = [
                f"Source {i}:",
                f"Title: {result.get('page_title', 'N/A')}",
                f"Section: {result.get('section_title', 'N/A')}",
                f"Content: {result.get('content', 'N/A')[:500]}..."
            ]
            
            # Add graph context if available
            graph_context = result.get("graph_context", {})
            if graph_context:
                entities = graph_context.get("related_entities", [])
                relationships = graph_context.get("related_relationships", [])
                
                if entities:
                    entity_names = [e.get("name", e.get("id", "")) for e in entities]
                    source_parts.append(f"Related entities: {', '.join(entity_names[:3])}")
                
                if relationships:
                    rel_count = len(relationships)
                    source_parts.append(f"Connected through {rel_count} relationship(s)")
            
            # Add scoring information
            if "graph_enhanced_score" in result:
                source_parts.append(f"Relevance score: {result['graph_enhanced_score']:.3f}")
            
            formatted_sources.append("\n".join(source_parts))
        
        return "\n\n=================\n\n".join(formatted_sources)
    
    def _format_basic_sources(self, results: List[Dict]) -> str:
        """Format basic sources without graph enhancement (fallback)."""
        if not results:
            return "No relevant sources found."
        
        formatted_sources = []
        
        for i, result in enumerate(results, 1):
            source_parts = [
                f"Source {i}:",
                f"Title: {result.get('page_title', 'N/A')}",
                f"Section: {result.get('section_title', 'N/A')}",
                f"Content: {result.get('content', 'N/A')[:500]}..."
            ]
            formatted_sources.append("\n".join(source_parts))
        
        return "\n\n=================\n\n".join(formatted_sources)
    

    
    def _get_entity_name_from_id(self, entity_id: str) -> str:
        """Extract a readable name from entity ID."""
        # Simple heuristic: remove prefixes and convert underscores to spaces
        if "_" in entity_id:
            parts = entity_id.split("_")
            if len(parts) > 1:
                return " ".join(parts[1:]).title()
        return entity_id
    
    def create_graph_enhanced_prompt(
        self,
        query: str,
        graph_context: GraphContext,
        base_prompt_template: str
    ) -> str:
        """
        Create a graph-enhanced prompt for the LLM.
        
        Args:
            query (str): User query
            graph_context (GraphContext): Formatted graph context
            base_prompt_template (str): Base prompt template
            
        Returns:
            str: Enhanced prompt with graph context
        """
        try:
            # Prepare graph context sections
            context_sections = []
            if graph_context.entities_summary:
                context_sections.append(f"ENTITIES: {graph_context.entities_summary}")
            if graph_context.relationships_summary:
                context_sections.append(f"RELATIONSHIPS: {graph_context.relationships_summary}")
            
            # Combine context
            graph_context_text = "\n\n".join(context_sections) if context_sections else ""
            
            # Create enhanced prompt
            enhanced_prompt = base_prompt_template.format(
                query=query,
                sources=graph_context.enhanced_sources,
                graph_context=graph_context_text
            )
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to create graph-enhanced prompt: {str(e)}")
            # Fallback to basic prompt
            return base_prompt_template.format(
                query=query,
                sources=graph_context.enhanced_sources,
                graph_context=""
            )
    
    def format_relationship_aware_response(
        self,
        response: str,
        graph_context: GraphContext
    ) -> Dict[str, Any]:
        """
        Format the LLM response with relationship-aware enhancements.
        
        Args:
            response (str): LLM response
            graph_context (GraphContext): Graph context used
            
        Returns:
            Dict[str, Any]: Enhanced response with graph metadata
        """
        try:
            enhanced_response = {
                "answer": response,
                "graph_enhanced": True,
                "entities_referenced": graph_context.metadata.get("total_entities", 0),
                "relationships_used": graph_context.metadata.get("total_relationships", 0),
                "combined_relevance_score": graph_context.metadata.get("combined_score", 0.0),
                "retrieval_metadata": graph_context.metadata.get("retrieval_metadata", {})
            }
            

            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Failed to format relationship-aware response: {str(e)}")
            return {
                "answer": response,
                "graph_enhanced": False,
                "error": str(e)
            }
    
