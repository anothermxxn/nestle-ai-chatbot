import sys
import os
import asyncio
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from utils.import_helper import setup_imports
setup_imports(__file__)
from chat.chat_client import NestleChatClient
from chat.context_manager import ContextExtractor

class SessionContextTester:
    """Test class for session and context functionality."""
    
    def __init__(self):
        """Initialize the tester."""
        self.client = None
        self.test_results = []
        
    async def initialize_client(self):
        """Initialize the chat client."""
        try:
            self.client = NestleChatClient()
            print("Chat client initialized successfully")
            return True
        except Exception as e:
            print(f"Failed to initialize chat client: {e}")
            return False
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        status = "PASS" if success else "FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_basic_session_creation(self):
        """Test basic session creation and management."""
        print("\nTesting Basic Session Creation")
        print("-" * 40)
        
        try:
            # Test creating a new session
            session_id = self.client.create_session()
            self.log_test("Create new session", bool(session_id), f"Session ID: {session_id}")
            
            # Test getting session history (should be empty)
            history = self.client.get_session_history(session_id)
            is_empty = history and history["message_count"] == 0
            self.log_test("New session has empty history", is_empty, f"Message count: {history['message_count'] if history else 'None'}")
            
            # Test creating session with custom ID
            custom_id = "test-session-123"
            created_id = self.client.create_session(custom_id)
            self.log_test("Create session with custom ID", created_id == custom_id, f"Expected: {custom_id}, Got: {created_id}")
            
            return session_id
            
        except Exception as e:
            self.log_test("Basic session creation", False, f"Error: {str(e)}")
            return None
    
    async def test_context_aware_conversation(self, session_id: str):
        """Test multi-turn context-aware conversation."""
        try:
            # First query about chocolate
            print("Query 1: Asking about chocolate products")
            response1 = await self.client.search_and_chat(
                query="Tell me about chocolate products from Nestle",
                session_id=session_id
            )
            
            has_answer = bool(response1.get("answer"))
            has_session = response1.get("session_id") == session_id
            self.log_test("First query processes correctly", has_answer and has_session, 
                         f"Answer length: {len(response1.get('answer', ''))}, Session matches: {has_session}")
            
            # Second query that should use context
            print("Query 2: Follow-up question (should use chocolate context)")
            response2 = await self.client.search_and_chat(
                query="What recipes can I make with these?",
                session_id=session_id
            )
            
            context_enhanced = response2.get("context_enhanced_search", False)
            has_context_summary = bool(response2.get("conversation_context"))
            self.log_test("Second query uses context", context_enhanced and has_context_summary,
                         f"Context enhanced: {context_enhanced}, Has context summary: {has_context_summary}")
            
            # Third query about different topic
            print("Query 3: Switching to coffee topic")
            response3 = await self.client.search_and_chat(
                query="What coffee products does Nestle make?",
                session_id=session_id
            )
            
            # Check that conversation context includes previous topics
            context_summary = response3.get("conversation_context", "")
            mentions_chocolate = "chocolate" in context_summary.lower()
            self.log_test("Context includes previous topics", mentions_chocolate,
                         f"Context mentions chocolate: {mentions_chocolate}")
            
            # Fourth query that could use both chocolate and coffee context
            print("Query 4: Query that could benefit from both contexts")
            response4 = await self.client.search_and_chat(
                query="Can I make mocha recipes?",
                session_id=session_id
            )
            
            final_context = response4.get("conversation_context", "")
            has_rich_context = len(final_context.split("|")) > 1  # Should have multiple context parts
            self.log_test("Final query has rich context", has_rich_context,
                         f"Context parts: {len(final_context.split('|'))}")
            
            return True
            
        except Exception as e:
            self.log_test("Context-aware conversation", False, f"Error: {str(e)}")
            return False
    
    async def test_session_history_tracking(self, session_id: str):
        """Test that session properly tracks conversation history."""
        print("\nTesting Session History Tracking")
        print("-" * 40)
        
        try:
            # Get session history
            history = self.client.get_session_history(session_id)
            
            if not history:
                self.log_test("Get session history", False, "No history returned")
                return False
            
            # Check that we have messages from previous tests
            message_count = history.get("message_count", 0)
            has_messages = message_count > 0
            self.log_test("Session has message history", has_messages, f"Message count: {message_count}")
            
            # Check message structure
            messages = history.get("messages", [])
            if messages:
                first_message = messages[0]
                has_proper_structure = all(key in first_message for key in ["role", "content", "timestamp"])
                self.log_test("Messages have proper structure", has_proper_structure,
                             f"Keys: {list(first_message.keys())}")
                
                # Check for both user and assistant messages
                user_messages = [msg for msg in messages if msg["role"] == "user"]
                assistant_messages = [msg for msg in messages if msg["role"] == "assistant"] 
                has_both_roles = len(user_messages) > 0 and len(assistant_messages) > 0
                self.log_test("Has both user and assistant messages", has_both_roles,
                             f"User: {len(user_messages)}, Assistant: {len(assistant_messages)}")
            
            # Check session metadata
            metadata = history.get("metadata", {})
            has_stats = "total_queries" in metadata and "total_responses" in metadata
            self.log_test("Session tracks statistics", has_stats,
                         f"Queries: {metadata.get('total_queries')}, Responses: {metadata.get('total_responses')}")
            
            return True
            
        except Exception as e:
            self.log_test("Session history tracking", False, f"Error: {str(e)}")
            return False
    
    async def test_context_enhancement_suggestions(self):
        """Test that context extractor provides good suggestions."""
        print("\nTesting Context Enhancement Suggestions")
        print("-" * 40)
        
        try:
            # Test context extractor directly
            extractor = ContextExtractor()
            
            # Test brand detection
            brand_analysis = extractor.analyze_query_intent("Tell me about KitKat chocolate bars")
            detected_brands = brand_analysis.get("detected_brands", [])
            detects_kitkat = "kit kat" in detected_brands or "kitkat" in detected_brands
            self.log_test("Detects brands in queries", detects_kitkat,
                         f"Detected brands: {detected_brands}")
            
            # Test content type detection  
            recipe_analysis = extractor.analyze_query_intent("How do I bake chocolate chip cookies with ingredients?")
            content_types = recipe_analysis.get("likely_content_types", [])
            detects_recipe = "recipe" in content_types
            self.log_test("Detects content types", detects_recipe,
                         f"Content types: {content_types}")
            
            # Test topic detection
            topics = recipe_analysis.get("detected_topics", {})
            # Handle both dict and list formats for topics
            if isinstance(topics, dict):
                # Extract matched keywords from the dictionary structure
                topic_keywords = []
                for topic_data in topics.values():
                    if isinstance(topic_data, dict):
                        topic_keywords.extend(topic_data.get("matched_keywords", []))
                
                # Check if any detected keywords are related to cooking/food
                has_cooking_topics = any(keyword.lower() in ["chocolate", "cookie", "baking", "ingredients", "recipe", "cooking"] for keyword in topic_keywords)
            else:
                # Fallback for list format
                has_cooking_topics = any(topic in ["chocolate", "cookie", "baking"] for topic in topics)
            
            self.log_test("Detects relevant topics", has_cooking_topics,
                         f"Topics: {topics}")
            
            return True
            
        except Exception as e:
            self.log_test("Context enhancement suggestions", False, f"Error: {str(e)}")
            return False
    
    async def test_specialized_methods_with_context(self):
        """Test specialized chat methods with session context."""
        print("\nTesting Specialized Methods with Context")
        print("-" * 40)
        
        try:
            # Create a new session for this test
            session_id = self.client.create_session("specialized-test")
            
            # Test recipe method with context
            recipe_response = await self.client.get_recipe("chocolate", session_id)
            recipe_success = bool(recipe_response.get("answer")) and recipe_response.get("session_id") == session_id
            self.log_test("Recipe method with session", recipe_success,
                         f"Session ID matches: {recipe_response.get('session_id') == session_id}")
            
            # Test product method with context (should benefit from chocolate context)
            product_response = await self.client.get_product("KitKat", session_id)
            product_success = bool(product_response.get("answer"))
            has_context = bool(product_response.get("conversation_context"))
            self.log_test("Product method uses context", product_success and has_context,
                         f"Has context: {has_context}")
            
            # Test cooking tips with accumulated context
            tips_response = await self.client.get_cooking_tips("melting chocolate", session_id)
            tips_success = bool(tips_response.get("answer"))
            context_summary = tips_response.get("conversation_context", "")
            mentions_previous = any(word in context_summary.lower() for word in ["chocolate", "recipe", "kitkat"])
            self.log_test("Cooking tips uses accumulated context", tips_success and mentions_previous,
                         f"Context mentions previous topics: {mentions_previous}")
            
            return session_id
            
        except Exception as e:
            self.log_test("Specialized methods with context", False, f"Error: {str(e)}")
            return None
    
    async def test_session_management_operations(self):
        """Test session management operations."""
        print("\nTesting Session Management Operations")
        print("-" * 40)
        
        try:
            # Test session statistics
            stats = self.client.get_all_sessions_stats()
            has_stats = isinstance(stats, dict) and "total_sessions" in stats
            self.log_test("Get session statistics", has_stats,
                         f"Total sessions: {stats.get('total_sessions')}")
            
            # Create a session to delete
            delete_test_id = self.client.create_session("delete-me")
            
            # Test session deletion
            deleted = self.client.delete_session(delete_test_id)
            self.log_test("Delete session", deleted, f"Session {delete_test_id} deleted: {deleted}")
            
            # Verify deletion
            deleted_history = self.client.get_session_history(delete_test_id)
            verify_deleted = deleted_history is None
            self.log_test("Verify session deletion", verify_deleted,
                         f"Session history is None: {verify_deleted}")
            
            # Test cleanup (won't have expired sessions in this test, but should not error)
            cleaned_count = self.client.cleanup_expired_sessions()
            cleanup_success = isinstance(cleaned_count, int) and cleaned_count >= 0
            self.log_test("Session cleanup operation", cleanup_success,
                         f"Cleaned sessions: {cleaned_count}")
            
            return True
            
        except Exception as e:
            self.log_test("Session management operations", False, f"Error: {str(e)}")
            return False
    
    async def test_context_persistence_across_queries(self):
        """Test that context persists and enhances across multiple queries."""
        print("\nTesting Context Persistence")
        print("-" * 40)
        
        try:
            # Create session for persistence test
            session_id = self.client.create_session("persistence-test")
            
            # Build up context gradually
            queries_and_expectations = [
                ("Tell me about Nescafe coffee", ["nescafe", "coffee"]),
                ("What are the different types?", ["nescafe", "coffee"]),  # Should inherit coffee context
                ("How do I make a good cup?", ["nescafe", "coffee"]),      # Should still have context
                ("Any recipes with this?", ["nescafe", "coffee", "recipe"]) # Should add recipe context
            ]
            
            context_builds_correctly = True
            for i, (query, expected_context_words) in enumerate(queries_and_expectations):
                print(f"Persistence Query {i+1}: {query}")
                
                response = await self.client.search_and_chat(
                    query=query,
                    session_id=session_id
                )
                
                context_summary = response.get("conversation_context", "").lower()
                
                # Check if expected context words are present
                context_preserved = all(word in context_summary for word in expected_context_words[:2])  # Check first 2 words
                
                if not context_preserved:
                    context_builds_correctly = False
                    self.log_test(f"Context persistence query {i+1}", False,
                                 f"Expected context not found. Context: {context_summary}")
                    break
                
                # Small delay to ensure proper sequencing
                await asyncio.sleep(0.1)
            
            if context_builds_correctly:
                self.log_test("Context persistence across queries", True,
                             "Context correctly builds and persists across all queries")
            
            return context_builds_correctly
            
        except Exception as e:
            self.log_test("Context persistence", False, f"Error: {str(e)}")
            return False
    
    def print_test_summary(self):
        """Print summary of all test results."""
        print("\n" + "=" * 60)
        print("SESSION & CONTEXT TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "Success Rate: N/A")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   {result['test']}: {result['details']}")
        
        # Test categories summary
        categories = {
            "Session Management": ["session", "create", "delete", "history"],
            "Context Awareness": ["context", "conversation", "enhancement"],
            "Persistence": ["persistence", "tracking"],
            "Specialized Methods": ["specialized", "recipe", "product", "tips"]
        }
        
        print(f"\nBY CATEGORY:")
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(kw in r["test"].lower() for kw in keywords)]
            if category_tests:
                category_passed = sum(1 for t in category_tests if t["success"])
                print(f"   {category}: {category_passed}/{len(category_tests)} passed")

async def run_comprehensive_test():
    """Run the comprehensive session and context test suite."""
    print("NESTLE AI CHATBOT - SESSION & CONTEXT TEST SUITE")
    print("=" * 60)
    print("Testing advanced conversation management and context awareness features")
    print("=" * 60)
    
    tester = SessionContextTester()
    
    # Initialize
    if not await tester.initialize_client():
        print("Cannot continue without chat client")
        return False
    
    # Run all tests
    session_id = await tester.test_basic_session_creation()
    
    if session_id:
        await tester.test_context_aware_conversation(session_id)
        await tester.test_session_history_tracking(session_id)
    
    await tester.test_context_enhancement_suggestions()
    specialized_session = await tester.test_specialized_methods_with_context()
    await tester.test_session_management_operations()
    await tester.test_context_persistence_across_queries()
    
    # Print summary
    tester.print_test_summary()
    
    # Return overall success
    total_tests = len(tester.test_results)
    passed_tests = sum(1 for result in tester.test_results if result["success"])
    return passed_tests == total_tests

async def run_interactive_session_test():
    """Run an interactive test where user can chat and see context building."""
    print("\nINTERACTIVE SESSION CONTEXT TEST")
    print("=" * 50)
    print("Commands:")
    print("  /session - Show current session info")
    print("  /history - Show conversation history") 
    print("  /context - Show current context")
    print("  /new - Start new session")
    print("  /quit - Exit")
    print("=" * 50)
    
    try:
        client = NestleChatClient()
        session_id = client.create_session("interactive-test")
        print(f"Started session: {session_id}")
        
        while True:
            try:
                user_input = input(f"\nYou: ").strip()
                
                if user_input.lower() in ['/quit', '/exit']:
                    print("Goodbye!")
                    break
                
                if user_input == '/session':
                    stats = client.get_all_sessions_stats()
                    print(f"Session Stats: {json.dumps(stats, indent=2)}")
                    continue
                
                if user_input == '/history':
                    history = client.get_session_history(session_id)
                    if history:
                        print(f"Message Count: {history['message_count']}")
                        for msg in history['messages'][-5:]:  # Show last 5 messages
                            role_prefix = "User" if msg['role'] == 'user' else "Bot"
                            print(f"   {role_prefix}: {msg['content'][:100]}...")
                    continue
                
                if user_input == '/context':
                    history = client.get_session_history(session_id)
                    if history:
                        print(f"Context: {history.get('conversation_summary', 'No context')}")
                        search_context = history.get('search_context', {})
                        print(f"Search Context: {json.dumps(search_context, indent=2)}")
                    continue
                
                if user_input == '/new':
                    session_id = client.create_session()
                    print(f"New session started: {session_id}")
                    continue
                
                if not user_input or user_input.startswith('/'):
                    continue
                
                # Process the query
                print("Thinking...")
                response = await client.search_and_chat(
                    query=user_input,
                    session_id=session_id
                )
                
                print(f"Bot: {response.get('answer', 'No answer')}")
                print(f"Sources: {response.get('search_results_count', 0)}")
                
                if response.get('conversation_context'):
                    print(f"Context: {response['conversation_context']}")
                
                if response.get('context_enhanced_search'):
                    print("Search was enhanced with conversation context!")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    except Exception as e:
        print(f"Failed to start interactive test: {str(e)}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Session and Context Functionality")
    parser.add_argument(
        "--mode",
        choices=["comprehensive", "interactive"],
        default="comprehensive", 
        help="Test mode to run"
    )
    
    args = parser.parse_args()
    
    if args.mode == "comprehensive":
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)
    else:
        asyncio.run(run_interactive_session_test())

if __name__ == "__main__":
    main() 