import os
import re
import asyncio
from urllib.parse import urlparse
from utilities import scrape_content

# Manually set the category for the scraped content
category = "brands"

def url_to_filename(url: str) -> str:
    """
    Convert a URL to a safe filename using only the last part of the path.
    
    Args:
        url (str): The URL to convert.
    
    Returns:
        str: The safe filename.
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    
    last_part = path.split('/')[-1] if path else ''
    if not last_part:
        last_part = 'index'
    
    name = re.sub(r'[^a-zA-Z0-9._-]', '_', last_part)
    return name

def save_content_to_file(sections, url: str):
    """
    Save grouped content (text, images, links, tables) to a single themed text file for the given URL.
    
    Args:
        sections (List[Dict]): List of grouped content sections.
        url (str): The URL the content was scraped from.
    """
    filename = url_to_filename(url) + ".txt"
    output_path = os.path.join("../../../data/raw", category, filename)
    
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

async def scrape_and_save(url: str):
    """
    Scrape grouped text, images, links, and tables from the URL and save to a single themed text file.
    
    Args:
        url (str): The URL to scrape.
    """
    sections = await scrape_content(url)
    save_content_to_file(sections, url)

if __name__ == "__main__":
    asyncio.run(scrape_and_save("https://www.madewithnestle.ca/aero")) 