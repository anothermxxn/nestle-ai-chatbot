import os
import re
import asyncio
from urllib.parse import urlparse, urljoin
from utilities import scrape_content, scrape_content_crawl4ai

def url_to_filename(url: str) -> str:
    """
    Convert a URL to a safe filename using the path after the domain.
    
    Args:
        url (str): The URL to convert.
    
    Returns:
        str: The safe filename.
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    
    if not path:
        return "index"
    
    # Remove leading slash and convert remaining slashes to underscores
    path = path.lstrip('/')
    name = re.sub(r'[^a-zA-Z0-9._/-]', '_', path)
    name = name.replace('/', '_')
    
    return name

def get_unique_filename(path: str, filename: str) -> str:
    """
    Generate a unique filename by adding a numeric suffix if the file already exists.
    
    Args:
        path (str): The path to the file.
        filename (str): The original filename.
    
    Returns:
        str: A unique filename that doesn't exist in the base_path.
    """
    counter = 1
    name, ext = os.path.splitext(filename)
    final_path = os.path.join(path, filename)
    
    while os.path.exists(final_path):
        new_filename = f"{name}_{counter}{ext}"
        final_path = os.path.join(path, new_filename)
        counter += 1
        
    return final_path

def save_content_to_file(sections, url: str):
    """
    Save grouped content (text, images, links, tables) to a single themed text file for the given URL.
    
    Args:
        sections (List[Dict]): List of grouped content sections.
        url (str): The URL the content was scraped from.
    """
    base_filename = url_to_filename(url) + ".txt"
    base_path = "../../../data/raw"
    output_path = get_unique_filename(base_path, base_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for section in sections:
            f.write(f"=== {section['heading']} ===\n")
            if section["content"]:
                f.write(section["content"] + "\n")
            if section["images"]:
                f.write("[Images]\n")
                for img in section["images"]:
                    f.write(f"{img}\n")
            if section["links"]:
                f.write("[Links]\n")
                for link in section["links"]:
                    f.write(f"{link}\n")
            if section["tables"]:
                for idx, table in enumerate(section["tables"]):
                    f.write(f"[Table {idx+1}]\n")
                    f.write("Headers: " + ", ".join(table['headers']) + "\n")
                    for row in table['rows']:
                        f.write(", ".join(row) + "\n")
            f.write("\n")
            
    print(f"Scraped content saved to {output_path}")

def save_crawl4ai_content_to_file(content, url: str):
    """
    Save Crawl4AI content to a file.
    
    Args:
        content (Crawl4AIContent): The content to save.
        url (str): The URL the content was scraped from.
    """
    base_filename = url_to_filename(url) + ".md"
    base_path = "../../../data/crawl4ai"
    output_path = get_unique_filename(base_path, base_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content.markdown.fit_markdown)

    print(f"Crawl4AI content saved to {output_path}")

def process_links(links, base_url, visited):
    """
    Normalize, deduplicate, and filter links to only include those on the same domain and not yet visited.
    
    Args:
        links (Iterable[str]): The links to process (can be relative or absolute).
        base_url (str): The base URL to resolve relative links.
        visited (set): Set of URLs that have already been visited.
    
    Returns:
        set: Set of normalized, deduplicated, and filtered absolute URLs on the same domain.
    """
    processed = set()
    
    for link in links:
        abs_link = urljoin(base_url, link)
        parsed = urlparse(abs_link)
        if parsed.netloc == "www.madewithnestle.ca" and abs_link not in visited:
            processed.add(abs_link)
            
    return processed

async def save_all_content_to_file(start_url: str, max_pages: int = 500):
    """
    Scrape the start URL and all subpages linked from it (same domain), saving each to a file.
    
    Args:
        start_url (str): The starting URL to scrape.
        max_pages (int): Maximum number of pages to scrape.
    """
    visited = set()
    to_visit = [start_url]
    count = 0
    
    while to_visit and count < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        print(f"Scraping: {current_url}")
        
        sections = await scrape_content(current_url)
        save_content_to_file(sections, current_url)
        
        result = await scrape_content_crawl4ai(current_url)
        save_crawl4ai_content_to_file(result, current_url)
        
        visited.add(current_url)
        count += 1
        
        # Collect links from the current page
        page_links = set()
        for section in sections:
            page_links.update(section.get("links", []))
        new_links = process_links(page_links, current_url, visited)
        to_visit.extend(new_links - set(to_visit))
        
    print(f"Scraping complete. {len(visited)} pages saved.")

if __name__ == "__main__":
    asyncio.run(save_all_content_to_file("https://www.madewithnestle.ca")) 