import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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

# Domain checking configuration
DOMAIN_CHECK_CONFIG = {
    "use_llm_classification": True,
    "llm_temperature": 0.0,
    "llm_max_tokens": 10,
}