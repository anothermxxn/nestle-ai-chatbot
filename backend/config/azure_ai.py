import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_CONFIG = {
    "endpoint": AZURE_OPENAI_ENDPOINT,
    "api_key": AZURE_OPENAI_API_KEY,
    "api_version": AZURE_OPENAI_API_VERSION,
    "deployment": AZURE_OPENAI_DEPLOYMENT,
}

# Azure Embedding configuration
AZURE_EMBEDDING_ENDPOINT = os.getenv("AZURE_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
AZURE_EMBEDDING_API_VERSION = os.getenv("AZURE_EMBEDDING_API_VERSION")
AZURE_EMBEDDING_MODEL_NAME = os.getenv("AZURE_EMBEDDING_MODEL_NAME")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")

AZURE_EMBEDDING_CONFIG = {
    "endpoint": AZURE_EMBEDDING_ENDPOINT,
    "full_endpoint": AZURE_EMBEDDING_ENDPOINT,
    "api_key": AZURE_EMBEDDING_API_KEY,
    "api_version": AZURE_EMBEDDING_API_VERSION,
    "model_name": AZURE_EMBEDDING_MODEL_NAME,
    "deployment": AZURE_EMBEDDING_DEPLOYMENT,
}

# Chat settings
CHAT_CONFIG = {
    "default_temperature": 0.3,
    "default_max_tokens": 1000,
    "session_timeout_hours": 24,
    "max_conversation_history": 20,
    "context_window": 5,
}

# Response templates
CHAT_PROMPTS = {
    "system_prompt": """
    You are a helpful AI assistant for Nestle, specializing in cooking, recipes, and food-related questions.
    Use the provided sources and graph context to answer the user's question accurately and helpfully.

    GRAPH CONTEXT:
    {graph_context}

    SOURCES:
    {sources}

    USER QUESTION: {query}

    Instructions:
    1. Answer based on the provided sources and graph context
    2. Use the graph insights to provide richer, more connected information
    3. Reference specific sources when possible
    4. If the graph context shows relationships between topics, mention these connections
    5. Be conversational and helpful
    6. Focus on Nestle products, recipes, and brand information
    7. Use bullets if the answer has multiple points
    8. If the answer is longer than 3 sentences, provide a summary
    9. If there isn't enough information, say you don't know
    10. Do not generate answers that don't use the sources provided

    Answer:
    """,
    
    "no_results_message": "I couldn't find any relevant information about your question. Please try rephrasing your question or asking about something else.",
    
    "error_message": "I'm sorry, I encountered an error while processing your question. Please try again.",
    
    "generation_error_message": "I found relevant sources but couldn't generate a complete answer. Please check the sources below."
}

def validate_azure_openai_config() -> bool:
    """
    Validate Azure OpenAI configuration.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_fields = ["endpoint", "api_key", "deployment"]
    
    for field in required_fields:
        if not AZURE_OPENAI_CONFIG.get(field):
            print(f"Missing required Azure OpenAI configuration: {field}")
            return False
    
    return True

def validate_azure_embedding_config() -> bool:
    """
    Validate Azure Embedding configuration.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_fields = ["endpoint", "api_key", "deployment", "model_name"]
    
    for field in required_fields:
        if not AZURE_EMBEDDING_CONFIG.get(field):
            print(f"Missing required Azure Embedding configuration: {field}")
            return False
    
    return True

def get_chat_client_config() -> dict:
    """
    Get complete configuration for chat client initialization.
    
    Returns:
        dict: Configuration dictionary for chat client
    """
    return {
        "azure_openai": AZURE_OPENAI_CONFIG,
        "chat_settings": CHAT_CONFIG,
        "prompts": CHAT_PROMPTS
    } 