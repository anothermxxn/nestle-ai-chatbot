import os
import json
import re
import urllib.parse
from typing import Dict, List
from datetime import datetime
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from collections import defaultdict
from url_parser import parse_url

def sanitize_url(url: str) -> str:
    """
    Sanitize URL for safe storage and retrieval.
    
    Args:
        url (str): Raw URL
        
    Returns:
        str: Sanitized URL safe for storage
    """
    # Decode URL-encoded characters
    decoded = urllib.parse.unquote(url)
    
    # Remove any protocol prefix
    decoded = re.sub(r'^https?://', '', decoded)
    
    # Remove special characters and spaces
    sanitized = re.sub(r'[^a-zA-Z0-9\-_/]', '_', decoded)
    
    # Replace multiple underscores with single one
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    return sanitized

def generate_safe_id(url: str, doc_index: int, chunk_index: int) -> str:
    """
    Generate a safe document ID from URL and indices.
    
    Args:
        url (str): Document URL
        doc_index (int): Document index
        chunk_index (int): Chunk index
        
    Returns:
        str: Safe document ID
    """
    safe_url = sanitize_url(url)
    return f"{safe_url}_{doc_index}_{chunk_index}"

def validate_markdown_file(file_path: str) -> bool:
    """
    Validate a markdown file exists and has content.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return len(content) > 0
    except Exception:
        return False

def create_content_index() -> Dict:
    """
    Create an index of all markdown files with metadata.
    Stores information about each scraped page for easy lookup.
    
    Returns:
        Dict: Index of content files with metadata
    """
    content_dir = "../../../data/raw"
    index = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_files": 0,
        "files": []
    }
    
    if not os.path.exists(content_dir):
        return index
        
    for filename in os.listdir(content_dir):
        if not filename.endswith(".md"):
            continue
            
        file_path = os.path.join(content_dir, filename)
        if not validate_markdown_file(file_path):
            continue
            
        # Get file metadata
        url = filename[:-3].replace("_", "/")
        content = read_markdown_file(file_path)
        url_info = parse_url(url, content)
        
        file_info = {
            "filename": filename,
            "path": file_path,
            "url": url,
            "content_type": url_info["content_type"],
            "brand": url_info["brand"],
            "title": url_info["normalized_title"],
            "keywords": url_info["keywords"],
            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }
        index["files"].append(file_info)
        
    index["total_files"] = len(index["files"])
    
    output_dir = "../../../data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "content_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        
    return index

def read_markdown_file(file_path: str) -> str:
    """
    Read and return the content of a markdown file.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        str: Content of the file
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def process_markdown_file(file_path: str, url: str) -> List[Dict]:
    """
    Process a markdown file into chunks using LangChain's text splitters.
    
    Args:
        file_path (str): Path to the markdown file
        url (str): Original URL of the content
        
    Returns:
        List[Dict]: List of chunks with metadata
    """
    content = read_markdown_file(file_path)
    
    # Parse URL for metadata
    url_info = parse_url(url, content)
    
    # Override content type for special cases
    if url.startswith("#") or url.startswith("javascript:"):
        url_info["content_type"] = "navigation"
        url_info["keywords"] = ["navigation"]
    elif "recipe" in url_info["content_type"] and not any(
        keyword in content.lower() 
        for keyword in ["ingredients", "preparation", "method", "directions", "recipe", "cooking"]
    ):
        url_info["content_type"] = "other"
        url_info["keywords"] = [k for k in url_info["keywords"] if k != "recipe"]
    
    # First split on markdown headers to preserve document structure
    markdown_splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=200)
    markdown_docs = markdown_splitter.create_documents([content])
    
    # Further split large sections if needed
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    safe_url = sanitize_url(url)
    
    for doc_idx, doc in enumerate(markdown_docs):
        # Look for headers in the content
        lines = doc.page_content.split("\n")
        title = None
        
        # Try to find a header line
        for line in lines:
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
        
        # If no header found, use first sentence as title
        if not title:
            content_text = " ".join(lines).strip()
            sentence_end = content_text.find(".")
            if sentence_end > 0 and sentence_end < 100:
                title = content_text[:sentence_end].strip()
            else:
                title = content_text[:50].strip() + "..."
        
        # Split into smaller chunks if needed
        if len(doc.page_content) > 1000:
            section_chunks = text_splitter.split_text(doc.page_content)
        else:
            section_chunks = [doc.page_content]
            
        for chunk_idx, chunk in enumerate(section_chunks):
            chunks.append({
                "id": generate_safe_id(url, doc_idx, chunk_idx),
                "url": safe_url,
                "content_type": url_info["content_type"],
                "brand": url_info["brand"],
                "page_title": url_info["normalized_title"],
                "section_title": title,
                "keywords": url_info["keywords"],
                "doc_index": doc_idx,
                "chunk_index": chunk_idx,
                "total_chunks": len(section_chunks),
                "content": chunk.strip(),
                "processed_at": datetime.utcnow().isoformat()
            })
    
    return chunks

def process_all_content() -> Dict:
    """
    Process all markdown files and prepare them for vector storage.
    
    Returns:
        Dict: Processing results and statistics
    """
    content_dir = "../../../data/raw"
    processed_dir = "../../../data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_files": 0,
        "total_chunks": 0,
        "content_types": defaultdict(int),
        "brands": defaultdict(int),
        "files": []
    }
    
    all_chunks = []
    
    for filename in os.listdir(content_dir):
        if not filename.endswith(".md"):
            continue
            
        file_path = os.path.join(content_dir, filename)
        url = filename[:-3].replace("_", "/")
        
        try:
            chunks = process_markdown_file(file_path, url)
            all_chunks.extend(chunks)
            
            # Update statistics
            if chunks:
                first_chunk = chunks[0]
                results["content_types"][first_chunk["content_type"]] += 1
                if first_chunk["brand"]:
                    results["brands"][first_chunk["brand"]] += 1
            
            file_info = {
                "filename": filename,
                "url": sanitize_url(url),
                "chunks": len(chunks),
                "content_type": chunks[0]["content_type"] if chunks else "unknown",
                "brand": chunks[0]["brand"] if chunks else None,
                "title": chunks[0]["page_title"] if chunks else None,
                "status": "success"
            }
            results["files"].append(file_info)
            results["total_chunks"] += len(chunks)
            results["total_files"] += 1
            
        except Exception as e:
            results["files"].append({
                "filename": filename,
                "url": sanitize_url(url),
                "status": "error",
                "error": str(e)
            })
    
    # Save all chunks to a single file
    chunks_file = os.path.join(processed_dir, "vector_chunks.json")
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Convert defaultdict to regular dict for JSON serialization
    results["content_types"] = dict(results["content_types"])
    results["brands"] = dict(results["brands"])
    
    # Save processing results
    results_file = os.path.join(processed_dir, "processing_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def get_content_hash(content: str) -> str:
    """
    Get a simple hash of the content for comparison.
    Removes whitespace and converts to lowercase for better matching.
    
    Args:
        content (str): The text content to hash.
    
    Returns:
        str: A hash of the normalized content.
    """
    return hash(content.lower().replace(" ", ""))

def remove_content_duplicates() -> Dict:
    """
    Find and remove files with duplicate content, keeping only one copy.
    
    Returns:
        Dict: Report of duplicate files and actions taken
    """
    content_dir = "../../../data/raw"
    if not os.path.exists(content_dir):
        return {"error": "Content directory not found"}
        
    # Track content hashes and their files
    content_map = defaultdict(list)
    
    # Collect all files and their content hashes
    print("Scanning files...")
    for filename in os.listdir(content_dir):
        if not filename.endswith(".md"):
            continue
            
        file_path = os.path.join(content_dir, filename)
        try:
            content = read_markdown_file(file_path)
            content_hash = get_content_hash(content)
            content_map[content_hash].append({
                "filename": filename,
                "path": file_path,
                "url": filename[:-3].replace("_", "/"),
                "size": os.path.getsize(file_path)
            })
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            
    # Find and handle duplicates
    duplicates = {
        h: files for h, files in content_map.items()
        if len(files) > 1
    }
    
    if not duplicates:
        return {
            "status": "success",
            "message": "No duplicate content found",
            "duplicates": {}
        }
        
    # Process duplicates
    results = {
        "status": "success",
        "message": f"Found {len(duplicates)} sets of duplicate content",
        "duplicates": {}
    }
    
    for content_hash, files in duplicates.items():
        # Sort by URL complexity (fewer slashes = simpler URL)
        files.sort(key=lambda x: x["url"].count("/"))
        
        # Keep the file with the simplest URL
        keep = files[0]
        remove = files[1:]
        
        # Record the duplicates
        results["duplicates"][keep["url"]] = {
            "kept": keep["filename"],
            "removed": [f["filename"] for f in remove]
        }
        
        # Remove duplicate files
        for file in remove:
            try:
                os.remove(file["path"])
                print(f"Removed duplicate file: {file['filename']}")
            except Exception as e:
                print(f"Error removing {file['filename']}: {str(e)}")
                
    return results

if __name__ == "__main__":
    # Remove duplicates
    print("Checking and removing duplicate files...")
    report = remove_content_duplicates()
    print(f"\nRemoved {len(report['duplicates'])} duplicate files.")
    
    # Process the cleaned content
    print("\nProcessing content...")
    results = process_all_content()
    print(f"Processed {results['total_files']} files into {results['total_chunks']} chunks") 