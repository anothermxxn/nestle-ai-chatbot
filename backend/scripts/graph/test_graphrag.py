import sys
import os
import json
import asyncio
import time
from typing import Dict, List, Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from utils.import_helper import setup_imports
setup_imports(__file__)

from search.graphrag_client import GraphRAGClient, GraphRAGResult
from search.search_client import AzureSearchClient
from chat.graphrag_formatter import GraphRAGFormatter, GraphContext
from graph.cosmos_client import CosmosGraphClient
from graph.models import EntityType

class GraphRAGTester:
    """Comprehensive tester for GraphRAG functionality."""
    
    def __init__(self):
        """Initialize the GraphRAG tester."""
        self.graphrag_client = None
        self.search_client = None
        self.formatter = None
        self.graph_client = None
        self.test_results = []
        self.test_timeout = 30  # 30 seconds timeout per test
        
    async def initialize_clients(self):
        """Initialize all required clients."""
        print("Initializing GraphRAG test clients...")
        
        try:
            # Initialize GraphRAG client
            self.graphrag_client = GraphRAGClient()
            print("✓ GraphRAG client initialized")
        except Exception as e:
            print(f"✗ Failed to initialize GraphRAG client: {str(e)}")
            return False
        
        try:
            # Initialize regular search client for comparison
            self.search_client = AzureSearchClient(enable_enhanced_ranking=True)
            print("✓ Azure Search client initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Azure Search client: {str(e)}")
            return False
        
        try:
            # Initialize formatter
            self.formatter = GraphRAGFormatter()
            print("✓ GraphRAG formatter initialized")
        except Exception as e:
            print(f"✗ Failed to initialize GraphRAG formatter: {str(e)}")
            return False
        
        try:
            # Initialize graph client
            self.graph_client = CosmosGraphClient()
            print("✓ Cosmos Graph client initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Cosmos Graph client: {str(e)}")
            return False
        
        return True
    
    def log_test_result(self, test_name: str, success: bool, details: Dict = None):
        """Log a test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        
        if details and not success:
            print(f"   Details: {details}")
    
    async def run_with_timeout(self, coro, timeout_seconds: int = None):
        """Run a coroutine with timeout."""
        timeout = timeout_seconds or self.test_timeout
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise Exception(f"Operation timed out after {timeout} seconds")
    
    async def test_graphrag_client_initialization(self):
        """Test GraphRAG client initialization."""
        test_name = "GraphRAG Client Initialization"
        
        try:
            # Test if client is properly initialized
            success = (
                self.graphrag_client is not None and
                hasattr(self.graphrag_client, "vector_client") and
                hasattr(self.graphrag_client, "graph_client") and
                hasattr(self.graphrag_client, "hybrid_search")
            )
            
            details = {
                "has_vector_client": hasattr(self.graphrag_client, "vector_client"),
                "has_graph_client": hasattr(self.graphrag_client, "graph_client"),
                "has_hybrid_search": hasattr(self.graphrag_client, "hybrid_search")
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_basic_hybrid_search(self):
        """Test basic hybrid search functionality."""
        test_name = "Basic Hybrid Search"
        
        try:
            print(f"   Starting hybrid search test with {self.test_timeout}s timeout...")
            query = "chocolate recipes"
            
            # Run with timeout to prevent hanging
            result = await self.run_with_timeout(
                self.graphrag_client.hybrid_search(
                    query=query,
                    top_results=3,
                    graph_expansion_depth=1
                ),
                timeout_seconds=self.test_timeout
            )
            
            success = (
                isinstance(result, GraphRAGResult) and
                hasattr(result, "vector_results") and
                hasattr(result, "related_entities") and
                hasattr(result, "contextual_relationships") and
                len(result.vector_results) > 0
            )
            
            details = {
                "query": query,
                "vector_results_count": len(result.vector_results) if result.vector_results else 0,
                "entities_count": len(result.related_entities) if result.related_entities else 0,
                "relationships_count": len(result.contextual_relationships) if result.contextual_relationships else 0,
                "combined_score": result.combined_score if hasattr(result, "combined_score") else None
            }
            
            self.log_test_result(test_name, success, details)
            return success, result
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False, None
    
    async def test_basic_vector_search_only(self):
        """Test basic vector search without GraphRAG to isolate the issue."""
        test_name = "Basic Vector Search Only"
        
        try:
            print(f"   Testing vector search only...")
            query = "chocolate recipes"
            
            # Test direct vector search
            result = await self.run_with_timeout(
                self.search_client.search(
                    query=query,
                    top=3,
                    enable_ranking=True
                ),
                timeout_seconds=10
            )
            
            success = isinstance(result, list) and len(result) > 0
            
            details = {
                "query": query,
                "results_count": len(result) if result else 0,
                "first_result_keys": list(result[0].keys()) if result and len(result) > 0 else []
            }
            
            self.log_test_result(test_name, success, details)
            return success, result
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False, None
    
    async def test_graph_entity_retrieval_simple(self):
        """Test simple graph entity retrieval."""
        test_name = "Simple Graph Entity Retrieval"
        
        try:
            print(f"   Testing simple entity retrieval...")
            
            # Test getting a small number of entities
            entities = await self.run_with_timeout(
                self.graph_client.find_entities_by_type(EntityType.PRODUCT, limit=2),
                timeout_seconds=10
            )
            
            success = isinstance(entities, list) and len(entities) >= 0
            
            details = {
                "entities_count": len(entities),
                "entity_sample": [e.get("id", "unknown") for e in entities[:2]] if entities else []
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_graph_context_formatting(self, graphrag_result: GraphRAGResult):
        """Test graph context formatting."""
        test_name = "Graph Context Formatting"
        
        try:
            query = "chocolate recipes"
            graph_context = self.formatter.format_graphrag_context(graphrag_result, query)
            
            success = (
                isinstance(graph_context, GraphContext) and
                hasattr(graph_context, "entities_summary") and
                hasattr(graph_context, "relationships_summary") and
                hasattr(graph_context, "enhanced_sources") and
                hasattr(graph_context, "metadata")
            )
            
            details = {
                "has_entities_summary": bool(graph_context.entities_summary),
                "has_relationships_summary": bool(graph_context.relationships_summary),
                "has_enhanced_sources": bool(graph_context.enhanced_sources),
                "metadata_keys": list(graph_context.metadata.keys()) if graph_context.metadata else []
            }
            
            self.log_test_result(test_name, success, details)
            return success, graph_context
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False, None
    
    async def test_enhanced_prompt_creation(self, graph_context: GraphContext):
        """Test enhanced prompt creation."""
        test_name = "Enhanced Prompt Creation"
        
        try:
            query = "chocolate recipes"
            system_prompt = "You are a helpful assistant. Use the following sources and graph context to answer the user's question.\n\nQuery: {query}\n\nSources:\n{sources}\n\nGraph Context:\n{graph_context}"
            
            enhanced_prompt = self.formatter.create_graph_enhanced_prompt(
                query, graph_context, system_prompt
            )
            
            success = (
                isinstance(enhanced_prompt, str) and
                len(enhanced_prompt) > len(system_prompt) and
                "entities" in enhanced_prompt.lower() and
                "relationships" in enhanced_prompt.lower()
            )
            
            details = {
                "prompt_length": len(enhanced_prompt),
                "contains_entities": "entities" in enhanced_prompt.lower(),
                "contains_relationships": "relationships" in enhanced_prompt.lower(),
                "contains_query": query in enhanced_prompt
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_relationship_aware_response(self, graph_context: GraphContext):
        """Test relationship-aware response formatting."""
        test_name = "Relationship-Aware Response"
        
        try:
            sample_answer = "Here are some chocolate recipes that use Nestle products..."
            
            enhanced_response = self.formatter.format_relationship_aware_response(
                sample_answer, graph_context
            )
            
            success = (
                isinstance(enhanced_response, dict) and
                "combined_relevance_score" in enhanced_response and
                "retrieval_metadata" in enhanced_response
            )
            
            details = {
                "has_relevance_score": "combined_relevance_score" in enhanced_response,
                "has_metadata": "retrieval_metadata" in enhanced_response,
                "response_keys": list(enhanced_response.keys())
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_graphrag_vs_regular_search(self):
        """Compare GraphRAG search vs regular search."""
        test_name = "GraphRAG vs Regular Search Comparison"
        
        try:
            query = "Nestle chocolate products"
            
            # GraphRAG search
            start_time = time.time()
            graphrag_result = await self.graphrag_client.hybrid_search(
                query=query,
                top_results=5,
                graph_expansion_depth=1
            )
            graphrag_time = time.time() - start_time
            
            # Regular search
            start_time = time.time()
            regular_results = await self.search_client.search(
                query=query,
                top=5,
                enable_ranking=True
            )
            regular_time = time.time() - start_time
            
            success = (
                len(graphrag_result.vector_results) > 0 and
                len(regular_results) > 0
            )
            
            details = {
                "graphrag_results_count": len(graphrag_result.vector_results),
                "regular_results_count": len(regular_results),
                "graphrag_entities": len(graphrag_result.related_entities) if graphrag_result.related_entities else 0,
                "graphrag_relationships": len(graphrag_result.contextual_relationships) if graphrag_result.contextual_relationships else 0,
                "graphrag_time_ms": round(graphrag_time * 1000, 2),
                "regular_time_ms": round(regular_time * 1000, 2),
                "time_difference_ms": round((graphrag_time - regular_time) * 1000, 2)
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_graph_entity_retrieval(self):
        """Test direct graph entity retrieval."""
        test_name = "Graph Entity Retrieval"
        
        try:
            # Test getting entities by type
            entities = await self.graph_client.get_entities_by_type("Product", limit=5)
            
            success = isinstance(entities, list) and len(entities) >= 0
            
            details = {
                "entities_count": len(entities),
                "entity_types": list(set([e.get("entity_type") for e in entities if e.get("entity_type")])) if entities else []
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_graph_relationship_retrieval(self):
        """Test direct graph relationship retrieval."""
        test_name = "Graph Relationship Retrieval"
        
        try:
            # Test getting relationships
            relationships = await self.graph_client.get_relationships(limit=5)
            
            success = isinstance(relationships, list) and len(relationships) >= 0
            
            details = {
                "relationships_count": len(relationships),
                "relationship_types": list(set([r.get("relationship_type") for r in relationships if r.get("relationship_type")])) if relationships else []
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_content_type_filtering(self):
        """Test GraphRAG with content type filtering."""
        test_name = "Content Type Filtering"
        
        try:
            query = "baking tips"
            
            # Test with recipe filter
            result = await self.graphrag_client.hybrid_search(
                query=query,
                content_type="recipe",
                top_results=3,
                graph_expansion_depth=1
            )
            
            success = (
                isinstance(result, GraphRAGResult) and
                len(result.vector_results) >= 0
            )
            
            details = {
                "query": query,
                "content_type": "recipe",
                "results_count": len(result.vector_results),
                "entities_count": len(result.related_entities) if result.related_entities else 0
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_brand_filtering(self):
        """Test GraphRAG with brand filtering."""
        test_name = "Brand Filtering"
        
        try:
            query = "chocolate products"
            
            # Test with brand filter
            result = await self.graphrag_client.hybrid_search(
                query=query,
                brand="NESTEA",
                top_results=3,
                graph_expansion_depth=1
            )
            
            success = (
                isinstance(result, GraphRAGResult) and
                len(result.vector_results) >= 0
            )
            
            details = {
                "query": query,
                "brand": "NESTEA",
                "results_count": len(result.vector_results),
                "entities_count": len(result.related_entities) if result.related_entities else 0
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    async def test_graph_expansion_depth(self):
        """Test different graph expansion depths."""
        test_name = "Graph Expansion Depth"
        
        try:
            query = "chocolate recipes"
            
            # Test depth 0 (no expansion)
            result_depth_0 = await self.graphrag_client.hybrid_search(
                query=query,
                top_results=3,
                graph_expansion_depth=0
            )
            
            # Test depth 1 (one level expansion)
            result_depth_1 = await self.graphrag_client.hybrid_search(
                query=query,
                top_results=3,
                graph_expansion_depth=1
            )
            
            # Test depth 2 (two level expansion)
            result_depth_2 = await self.graphrag_client.hybrid_search(
                query=query,
                top_results=3,
                graph_expansion_depth=2
            )
            
            success = all([
                isinstance(result_depth_0, GraphRAGResult),
                isinstance(result_depth_1, GraphRAGResult),
                isinstance(result_depth_2, GraphRAGResult)
            ])
            
            details = {
                "depth_0_entities": len(result_depth_0.related_entities) if result_depth_0.related_entities else 0,
                "depth_1_entities": len(result_depth_1.related_entities) if result_depth_1.related_entities else 0,
                "depth_2_entities": len(result_depth_2.related_entities) if result_depth_2.related_entities else 0,
                "depth_0_relationships": len(result_depth_0.contextual_relationships) if result_depth_0.contextual_relationships else 0,
                "depth_1_relationships": len(result_depth_1.contextual_relationships) if result_depth_1.contextual_relationships else 0,
                "depth_2_relationships": len(result_depth_2.contextual_relationships) if result_depth_2.contextual_relationships else 0
            }
            
            self.log_test_result(test_name, success, details)
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, {"error": str(e)})
            return False
    
    def print_test_summary(self):
        """Print a summary of all test results."""
        print("\n" + "=" * 60)
        print("GRAPHRAG TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print(f"\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}")
                    if "error" in result["details"]:
                        print(f"    Error: {result['details']['error']}")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "PASS" if result["success"] else "FAIL"
            print(f"  {status}: {result['test_name']}")
            if result["details"] and "error" not in result["details"]:
                for key, value in result["details"].items():
                    print(f"    {key}: {value}")
    
    async def run_all_tests(self):
        """Run all GraphRAG tests."""
        print("Starting GraphRAG Comprehensive Test Suite")
        print("=" * 60)
        
        # Initialize clients
        if not await self.initialize_clients():
            print("Failed to initialize clients. Aborting tests.")
            return False
        
        print("\nRunning tests...\n")
        
        # Core functionality tests
        await self.test_graphrag_client_initialization()
        
        success, graphrag_result = await self.test_basic_hybrid_search()
        if success and graphrag_result:
            success, graph_context = await self.test_graph_context_formatting(graphrag_result)
            if success and graph_context:
                await self.test_enhanced_prompt_creation(graph_context)
                await self.test_relationship_aware_response(graph_context)
        
        # Comparison tests
        await self.test_graphrag_vs_regular_search()
        
        # Graph-specific tests
        await self.test_graph_entity_retrieval()
        await self.test_graph_relationship_retrieval()
        
        # Filtering tests
        await self.test_content_type_filtering()
        await self.test_brand_filtering()
        
        # Advanced tests
        await self.test_graph_expansion_depth()
        
        # Print summary
        self.print_test_summary()
        
        # Return overall success
        return all(result["success"] for result in self.test_results)

async def quick_test():
    """Run a quick subset of tests."""
    print("Running Quick GraphRAG Test")
    print("-" * 40)
    
    tester = GraphRAGTester()
    
    if not await tester.initialize_clients():
        print("Failed to initialize clients.")
        return False
    
    # Run diagnostic tests first
    await tester.test_graphrag_client_initialization()
    await tester.test_basic_vector_search_only()
    await tester.test_graph_entity_retrieval_simple()
    
    # Try the hybrid search with timeout
    print("\nTesting GraphRAG hybrid search...")
    success, graphrag_result = await tester.test_basic_hybrid_search()
    if success and graphrag_result:
        await tester.test_graph_context_formatting(graphrag_result)
    
    tester.print_test_summary()
    return all(result["success"] for result in tester.test_results)

async def interactive_test():
    """Run interactive GraphRAG testing."""
    print("\nInteractive GraphRAG Test Mode")
    print("-" * 40)
    print("Commands:")
    print("  init - Initialize clients")
    print("  basic - Test basic hybrid search")
    print("  compare - Compare GraphRAG vs regular search")
    print("  entities - Test entity retrieval")
    print("  relationships - Test relationship retrieval")
    print("  filter <content_type> - Test content type filtering")
    print("  brand <brand_name> - Test brand filtering")
    print("  depth <number> - Test graph expansion depth")
    print("  all - Run all tests")
    print("  quit - Exit")
    print("-" * 40)
    
    tester = GraphRAGTester()
    initialized = False
    
    while True:
        try:
            command = input("\nCommand: ").strip()
            
            if command.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            
            if not command:
                continue
            
            parts = command.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == "init":
                initialized = await tester.initialize_clients()
            elif cmd == "basic":
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                await tester.test_basic_hybrid_search()
            elif cmd == "compare":
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                await tester.test_graphrag_vs_regular_search()
            elif cmd == "entities":
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                await tester.test_graph_entity_retrieval()
            elif cmd == "relationships":
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                await tester.test_graph_relationship_retrieval()
            elif cmd == "filter" and arg:
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                # Temporarily modify the test to use the provided content type
                original_test = tester.test_content_type_filtering
                async def custom_test():
                    query = "test query"
                    result = await tester.graphrag_client.hybrid_search(
                        query=query,
                        content_type=arg,
                        top_results=3,
                        graph_expansion_depth=1
                    )
                    success = isinstance(result, GraphRAGResult)
                    details = {
                        "content_type": arg,
                        "results_count": len(result.vector_results) if result.vector_results else 0
                    }
                    tester.log_test_result(f"Content Type Filter: {arg}", success, details)
                await custom_test()
            elif cmd == "brand" and arg:
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                # Similar custom test for brand
                query = "test query"
                result = await tester.graphrag_client.hybrid_search(
                    query=query,
                    brand=arg,
                    top_results=3,
                    graph_expansion_depth=1
                )
                success = isinstance(result, GraphRAGResult)
                details = {
                    "brand": arg,
                    "results_count": len(result.vector_results) if result.vector_results else 0
                }
                tester.log_test_result(f"Brand Filter: {arg}", success, details)
            elif cmd == "depth" and arg:
                if not initialized:
                    print("Please initialize clients first (init)")
                    continue
                try:
                    depth = int(arg)
                    query = "test query"
                    result = await tester.graphrag_client.hybrid_search(
                        query=query,
                        top_results=3,
                        graph_expansion_depth=depth
                    )
                    success = isinstance(result, GraphRAGResult)
                    details = {
                        "depth": depth,
                        "entities_count": len(result.related_entities) if result.related_entities else 0,
                        "relationships_count": len(result.contextual_relationships) if result.contextual_relationships else 0
                    }
                    tester.log_test_result(f"Graph Expansion Depth: {depth}", success, details)
                except ValueError:
                    print("Please provide a valid number for depth")
            elif cmd == "all":
                if not initialized:
                    initialized = await tester.initialize_clients()
                if initialized:
                    await tester.run_all_tests()
            else:
                print("Unknown command or missing argument")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GraphRAG Test Suite")
    parser.add_argument(
        "--mode",
        choices=["full", "quick", "interactive"],
        default="quick",
        help="Test mode to run"
    )
    
    args = parser.parse_args()
    
    if args.mode == "full":
        tester = GraphRAGTester()
        success = asyncio.run(tester.run_all_tests())
        sys.exit(0 if success else 1)
    elif args.mode == "quick":
        success = asyncio.run(quick_test())
        sys.exit(0 if success else 1)
    else:
        asyncio.run(interactive_test())

if __name__ == "__main__":
    main() 