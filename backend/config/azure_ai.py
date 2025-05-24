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
    "default_system_prompt": """
        You are a helpful AI agent for Made with Nestlé website.
        Answer the query using only the sources provided below.
        Use bullets if the answer has multiple points.
        If the answer is longer than 3 sentences, provide a summary.
        Answer ONLY with the facts listed in the list of sources below.
        Cite your source when you answer the question.
        If there isn't enough information below, say you don't know.
        Do not generate answers that don't use the sources below.
        Focus on Nestle products, recipes, and brand information.
        Be helpful and friendly in your responses.
        
        Consider the conversation context when formulating your response.
        If this relates to previous questions in the conversation, acknowledge that context naturally.

        Conversation Context: {context_summary}
        
        Current Query: {query}
        Sources:
        {sources}
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