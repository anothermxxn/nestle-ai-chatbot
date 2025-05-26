import asyncio
import json
import os
import sys
from typing import List, Dict
from openai import AzureOpenAI
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from utils.import_helper import setup_imports
setup_imports(__file__)
from config import (
    DEFAULT_VECTOR_CHUNKS_FILE,
    AZURE_EMBEDDING_ENDPOINT,
    AZURE_EMBEDDING_API_KEY,
    AZURE_EMBEDDING_API_VERSION,
    AZURE_EMBEDDING_DEPLOYMENT,
    BATCH_SIZE
)
from search.search_client import AzureSearchClient

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client using embedding config
client = AzureOpenAI(
    api_key=AZURE_EMBEDDING_API_KEY,
    azure_endpoint=AZURE_EMBEDDING_ENDPOINT,
    api_version=AZURE_EMBEDDING_API_VERSION
)

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for a list of texts using Azure Embedding service.
    
    Args:
        texts (List[str]): List of texts to get embeddings for
        
    Returns:
        List[List[float]]: List of embeddings
    """
    try:
        response = client.embeddings.create(
            model=AZURE_EMBEDDING_DEPLOYMENT,
            input=texts
        )
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        print(f"Error getting embeddings: {str(e)}")
        return None

async def prepare_documents(chunks: List[Dict]) -> List[Dict]:
    """
    Prepare documents by adding vector embeddings.
    
    Args:
        chunks (List[Dict]): List of content chunks
        
    Returns:
        List[Dict]: Chunks with vector embeddings
    """
    batch_size = BATCH_SIZE // 5  # Azure OpenAI embedding batch size should be smaller
    prepared_chunks = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        # Prepare texts for embedding
        content_texts = [chunk["content"] for chunk in batch]
        title_texts = [chunk.get("page_title", "") for chunk in batch]
        section_texts = [chunk.get("section_title", "") for chunk in batch]
        
        # Get embeddings
        print(f"\nGenerating embeddings for batch {i//batch_size + 1}...")
        content_vectors = get_embeddings(content_texts)
        title_vectors = get_embeddings(title_texts)
        section_vectors = get_embeddings(section_texts)
        
        if not all([content_vectors, title_vectors, section_vectors]):
            print("Failed to generate embeddings for batch")
            continue
            
        # Add vectors to chunks
        for j, chunk in enumerate(batch):
            chunk["content_vector"] = content_vectors[j]
            chunk["page_title_vector"] = title_vectors[j]
            chunk["section_title_vector"] = section_vectors[j]
            prepared_chunks.append(chunk)
            
    return prepared_chunks

async def load_processed_chunks() -> List[Dict]:
    """
    Load processed content chunks from the JSON file.
    
    Returns:
        List[Dict]: List of content chunks.
    """
    chunks_file = DEFAULT_VECTOR_CHUNKS_FILE
    
    if not os.path.exists(chunks_file):
        print(f"No processed chunks found at {chunks_file}. Please run the data processing first.")
        return []
    
    with open(chunks_file, "r", encoding="utf-8") as f:
        return json.load(f)

async def main():
    """Upload processed content chunks to Azure Cognitive Search."""
    # Load processed content chunks
    print(f"\nLoading processed content chunks from {DEFAULT_VECTOR_CHUNKS_FILE}...")
    chunks = await load_processed_chunks()
    if not chunks:
        return
        
    # Prepare documents with embeddings
    print(f"\nPreparing {len(chunks)} documents with embeddings...")
    prepared_chunks = await prepare_documents(chunks)
    
    if not prepared_chunks:
        print("No documents were prepared successfully")
        return
    
    # Initialize search client and upload all documents
    client = AzureSearchClient()
    print(f"\nUploading {len(prepared_chunks)} documents...")
    
    success = await client.index_documents(prepared_chunks)
    
    if success:
        print("All documents uploaded successfully!")
    else:
        print("Some documents failed to upload. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main()) 