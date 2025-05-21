import asyncio
import json
import os
from typing import List, Dict
from azure_search import AzureSearchClient

async def load_processed_chunks() -> List[Dict]:
    """
    Load processed content chunks from the JSON file.
    
    Returns:
        List[Dict]: List of content chunks.
    """
    chunks_file = "../../../data/processed/vector_chunks.json"
    
    if not os.path.exists(chunks_file):
        print("No processed chunks found. Please run the data processing first.")
        return []
    
    with open(chunks_file, "r", encoding="utf-8") as f:
        return json.load(f)


async def main():
    """Upload processed content chunks to Azure Cognitive Search."""
    # Load processed content chunks
    print("\nLoading processed content chunks...")
    chunks = await load_processed_chunks()
    if not chunks:
        return
    
    # Initialize search client
    client = AzureSearchClient()
    
    # Upload chunks in batches
    batch_size = 100
    total_chunks = len(chunks)
    print(f"\nUploading {total_chunks} documents in batches of {batch_size}...")
    
    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        success = await client.index_documents(batch)
        if success:
            print(f"Uploaded batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size}")
        else:
            print(f"Failed to upload batch {i//batch_size + 1}")
    
    print("\nUpload complete!")


if __name__ == "__main__":
    asyncio.run(main()) 