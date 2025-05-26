import sys
import os
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from utils.import_helper import setup_imports
setup_imports(__file__)
from chat.chat_router import router

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_endpoint(method, endpoint, data=None, params=None):
    """Test a single endpoint and return results."""
    try:
        if method == "GET":
            if params:
                response = client.get(endpoint, params=params)
            else:
                response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=data)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "success": response.status_code in [200, 422],
            "response": response.json() if response.status_code in [200, 422] else response.text
        }
    except Exception as e:
        return {"error": str(e)}

def quick_test():
    """Run a quick test of all endpoints."""
    print("QUICK CHAT ROUTER TEST")
    print("=" * 50)
    
    tests = [
        {
            "name": "Health Check",
            "method": "GET",
            "endpoint": "/chat/health"
        },
        {
            "name": "Examples",
            "method": "GET", 
            "endpoint": "/chat/examples"
        },
        {
            "name": "Chat Search",
            "method": "POST",
            "endpoint": "/chat/search",
            "data": {"query": "test", "top_search_results": 1}
        },
        {
            "name": "Recipe Search",
            "method": "POST",
            "endpoint": "/chat/recipes",
            "data": {"ingredient": "chocolate"}
        },
        {
            "name": "Product Search",
            "method": "POST",
            "endpoint": "/chat/products",
            "data": {"product_name": "test"}
        },
        {
            "name": "Cooking Tips",
            "method": "POST",
            "endpoint": "/chat/cooking-tips", 
            "data": {"topic": "baking"}
        },
        {
            "name": "Nutrition Info",
            "method": "POST",
            "endpoint": "/chat/nutrition",
            "data": {"food_item": "apple"}
        },
        {
            "name": "Quick Search",
            "method": "GET",
            "endpoint": "/chat/quick-search",
            "params": {"q": "test", "limit": 1}
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\nTesting {test['name']}...")
        
        result = test_endpoint(
            test["method"],
            test["endpoint"],
            test.get("data"),
            test.get("params")
        )
        
        if "error" in result:
            print(f"   ERROR: {result['error']}")
            results.append(False)
        elif result["success"]:
            status_code = result["status_code"]
            if status_code == 200:
                print(f"   SUCCESS (200)")
                # Show brief response for successful calls
                if isinstance(result["response"], dict):
                    if "answer" in result["response"]:
                        answer_preview = result["response"]["answer"][:50] + "..." if len(result["response"]["answer"]) > 50 else result["response"]["answer"]
                        print(f"      Answer: {answer_preview}")
                    elif "status" in result["response"]:
                        print(f"      Status: {result['response']['status']}")
                    elif isinstance(result["response"], dict) and len(result["response"]) > 0:
                        print(f"      Data: {list(result['response'].keys())}")
            elif status_code == 422:
                print(f"   VALIDATION ERROR (422) - Expected for some tests")
            results.append(True)
        else:
            print(f"   FAILED ({result['status_code']})")
            print(f"      Response: {result.get('response', 'No response')}")
            results.append(False)
    
    print(f"\n{'=' * 50}")
    print("QUICK TEST SUMMARY")
    print(f"{'=' * 50}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"All {total} tests passed!")
    else:
        print(f"{passed}/{total} tests passed")
    
    return passed == total

def interactive_test():
    """Run interactive testing mode."""
    print("\nINTERACTIVE ROUTER TEST MODE")
    print("-" * 40)
    print("Commands:")
    print("  health - Test health endpoint")
    print("  examples - Test examples endpoint") 
    print("  search <query> - Test search endpoint")
    print("  recipe <ingredient> - Test recipe endpoint")
    print("  product <name> - Test product endpoint")
    print("  tips <topic> - Test cooking tips endpoint")
    print("  nutrition <food> - Test nutrition endpoint")
    print("  quick <query> - Test quick search endpoint")
    print("  quit - Exit")
    print("-" * 40)
    
    while True:
        try:
            command = input("\nCommand: ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not command:
                continue
            
            parts = command.split(' ', 1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == 'health':
                result = test_endpoint("GET", "/chat/health")
            elif cmd == 'examples':
                result = test_endpoint("GET", "/chat/examples")
            elif cmd == 'search' and arg:
                result = test_endpoint("POST", "/chat/search", {"query": arg, "top_search_results": 2})
            elif cmd == 'recipe' and arg:
                result = test_endpoint("POST", "/chat/recipes", {"ingredient": arg})
            elif cmd == 'product' and arg:
                result = test_endpoint("POST", "/chat/products", {"product_name": arg})
            elif cmd == 'tips' and arg:
                result = test_endpoint("POST", "/chat/cooking-tips", {"topic": arg})
            elif cmd == 'nutrition' and arg:
                result = test_endpoint("POST", "/chat/nutrition", {"food_item": arg})
            elif cmd == 'quick' and arg:
                result = test_endpoint("GET", "/chat/quick-search", params={"q": arg, "limit": 2})
            else:
                print("Unknown command or missing argument")
                continue
            
            # Display result
            if "error" in result:
                print(f"ERROR: {result['error']}")
            else:
                print(f"Status: {result['status_code']}")
                if result['status_code'] == 200 and isinstance(result['response'], dict):
                    if "answer" in result['response']:
                        print(f"Answer: {result['response']['answer']}")
                        print(f"Sources: {result['response'].get('search_results_count', 0)}")
                    else:
                        print(f"Response: {json.dumps(result['response'], indent=2)[:200]}...")
                elif result['status_code'] != 200:
                    print(f"Response: {result.get('response', 'No response')}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick Test for Nestle AI Chatbot Router")
    parser.add_argument(
        "--mode",
        choices=["quick", "interactive"],
        default="quick",
        help="Test mode to run"
    )
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        success = quick_test()
        sys.exit(0 if success else 1)
    else:
        interactive_test()

if __name__ == "__main__":
    main() 