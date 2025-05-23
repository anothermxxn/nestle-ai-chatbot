import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Search settings from environment variables
endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
api_version = os.getenv("AZURE_SEARCH_API_VERSION")

def create_index(index_settings):
    """Create a new search index."""
    url = f"{endpoint}/indexes/{index_name}?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    try:
        logger.info(f"Creating index '{index_name}'...")
        response = requests.put(url, headers=headers, json=index_settings)
        response.raise_for_status()
        logger.info("Index created successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create index: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        raise

def main():
    from config import INDEX_SETTINGS
    try:
        result = create_index(INDEX_SETTINGS)
        logger.info("Index creation completed")
    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        raise

if __name__ == "__main__":
    main() 