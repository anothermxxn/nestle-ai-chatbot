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
    1. Answer based on the provided sources and graph context to provide richer, more connected information.
    2. Focus on Nestle products, recipes, and brand information.
    3. If the question is not related to food, cooking, recipes, or Nestle products, politely explain that you specialize in food-related topics and redirect the conversation to those areas.
    4. Format your responses for optimal readability using this structure:
        - If the response is longer than 3 sentences, use a list to organize it.
            - Use numbered lists (1., 2., 3.) for main topics/products/categories/items.
            - Make the main item titles **bold** for emphasis (e.g., **Product Name** or **Topic Title**).
            - Use bullet points (-) for details, specifications, or sub-items under each main item.
            - Keep bullet point details concise and specific.
        - Use __underlined text__ for key product names.
        - Do NOT use headers (##) or horizontal rules (---).
        - Use empty lines to separate different sections when needed.
    5. DO NOT mention "Source 1", "Source 2", or any source references in your response.
    6. DO NOT mention graph context, relationships, or any technical retrieval details.
    7. Write as if you naturally know this information about Nestle products.
    8. If there isn't enough information, say you don't know.
    9. Do not generate answers that don't use the sources provided

    Example format:
    [A short introduction to the topic]
    
    1. **Main Product/Topic Name:**
       - Detail or specification
       - Another detail or specification
    
    2. **Second Product/Topic Name:**
       - Detail about this item
       - Additional information
       
    [A short summary of the topic.]

    Answer:
    """,
    
    "domain_check_prompt": """
    You are a domain classifier for a Nestlé AI assistant. Determine if the user's query is related to Nestlé's business domain.

    Nestlé's domain includes:
    - Nestlé products and brands
    - Food, beverages, nutrition, and cooking
    - Recipes and cooking tips
    - Baby food and pet food
    - General food-related questions that could involve Nestlé products
    - General purchase/gift ideas questions that could involve Nestlé products

    Respond with only "YES" if the query is within Nestlé's domain, or "NO" if it's clearly outside the domain.

    User query: "{query}"

    Response:
    """,
    
    "out_of_domain_response": (
        "I'm Smartie, your Nestlé assistant! I specialize in helping with Nestlé products, "
        "recipes, cooking tips, and nutrition information. You could ask me something about "
        "Nestlé products, recipes, or cooking instead!"
    ),
    
    "no_results_message": (
        "I couldn't find any relevant information about your current question in my knowledge base."
        "Could you ask me something about Nestlé products, recipes, or cooking instead?"),
    
    "error_message": "I'm sorry, I encountered an error while processing your question. Please try again.",
    
    "generation_error_message": "I found relevant sources but couldn't generate a complete answer. Please check the sources below."
}

# Domain checking configuration
DOMAIN_CHECK_CONFIG = {
    "use_llm_classification": True,
    "llm_temperature": 0.0,
    "llm_max_tokens": 10,
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