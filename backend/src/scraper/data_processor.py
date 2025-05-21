import os
import json
from typing import Dict, List, Set, Tuple
from datetime import datetime
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from collections import defaultdict

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
        with open(file_path, 'r', encoding='utf-8') as f:
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
        if not filename.endswith('.md'):
            continue
            
        file_path = os.path.join(content_dir, filename)
        if not validate_markdown_file(file_path):
            continue
            
        # Get file metadata
        file_info = {
            "filename": filename,
            "path": file_path,
            "url": filename[:-3].replace('_', '/'),  # Convert filename back to URL format
            "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        }
        index["files"].append(file_info)
        
    index["total_files"] = len(index["files"])
    
    # Save index
    output_dir = "../../../data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "content_index.json"), 'w', encoding='utf-8') as f:
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
    with open(file_path, 'r', encoding='utf-8') as f:
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
    
    for doc_idx, doc in enumerate(markdown_docs):
        # Get section title from first line if it's a header
        lines = doc.page_content.split('\n')
        title = lines[0] if lines[0].startswith('#') else "Section"
        
        # Split into smaller chunks if needed
        if len(doc.page_content) > 1000:
            section_chunks = text_splitter.split_text(doc.page_content)
        else:
            section_chunks = [doc.page_content]
            
        for chunk_idx, chunk in enumerate(section_chunks):
            chunks.append({
                "url": url,
                "section_title": title.lstrip('#').strip(),
                "doc_index": doc_idx,
                "chunk_index": chunk_idx,
                "total_chunks": len(section_chunks),
                "content": chunk.strip(),
                "source_file": file_path,
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
        "files": []
    }
    
    all_chunks = []
    
    for filename in os.listdir(content_dir):
        if not filename.endswith('.md'):
            continue
            
        file_path = os.path.join(content_dir, filename)
        url = filename[:-3].replace('_', '/')
        
        try:
            chunks = process_markdown_file(file_path, url)
            all_chunks.extend(chunks)
            
            file_info = {
                "filename": filename,
                "url": url,
                "chunks": len(chunks),
                "status": "success"
            }
            results["files"].append(file_info)
            results["total_chunks"] += len(chunks)
            results["total_files"] += 1
            
        except Exception as e:
            results["files"].append({
                "filename": filename,
                "url": url,
                "status": "error",
                "error": str(e)
            })
    
    # Save all chunks to a single file
    chunks_file = os.path.join(processed_dir, "vector_chunks.json")
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    # Save processing results
    results_file = os.path.join(processed_dir, "processing_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def get_content_hash(content: str) -> str:
    """
    Get a simple hash of the content for comparison.
    Removes whitespace and converts to lowercase for better matching.
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
    content_map = defaultdict(list)  # content hash -> list of files
    
    # First pass: collect all files and their content hashes
    print("Scanning files...")
    for filename in os.listdir(content_dir):
        if not filename.endswith('.md'):
            continue
            
        file_path = os.path.join(content_dir, filename)
        try:
            # Read and hash content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                content_hash = hash(content.lower().replace(" ", ""))
                content_map[content_hash].append(file_path)
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    # Remove duplicates, keeping the first file in each group
    removed_files = []
    for content_hash, files in content_map.items():
        if len(files) > 1:
            # Keep the first file, remove others
            for duplicate in files[1:]:
                try:
                    os.remove(duplicate)
                    removed_files.append(duplicate)
                    print(f"Removed duplicate: {duplicate}")
                except Exception as e:
                    print(f"Error removing {duplicate}: {e}")
    
    # Prepare report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "initial_file_count": sum(1 for f in os.listdir(content_dir) if f.endswith('.md')) + len(removed_files),
        "duplicates_removed": len(removed_files),
        "remaining_files": sum(1 for f in os.listdir(content_dir) if f.endswith('.md')),
        "removed_files": removed_files
    }
    
    # Save report
    report_path = os.path.join("../../../data/processed", "duplicate_removal_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report

if __name__ == "__main__":
    # First remove duplicates
    print("Checking and removing duplicate files...")
    report = remove_content_duplicates()
    print(f"\nRemoved {report['duplicates_removed']} duplicate files.")
    print(f"Original count: {report['initial_file_count']}")
    print(f"Remaining files: {report['remaining_files']}")
    
    # Then process the cleaned content
    print("\nProcessing content...")
    results = process_all_content()
    print(f"Processed {results['total_files']} files into {results['total_chunks']} chunks") 