import os
import asyncio
import argparse
import logging
from link_collector import LinkCollector
from content_processor import ContentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def collect_links(base_url: str, output_file: str, max_pages: int = 10000):
    """Collect links from the website and save to file.
    
    Args:
        base_url (str): Starting URL to collect links from
        output_file (str): Path to save collected links
        max_pages (int): Maximum number of pages to process
    """
    collector = LinkCollector(base_url=base_url, output_file=output_file)
    await collector.collect_links(max_pages=max_pages)

async def process_content(links_file: str, output_dir: str):
    """Process collected links with crawl4ai and generate markdown files.
    
    Args:
        links_file (str): Path to JSON file containing collected links
        output_dir (str): Directory to save markdown files
    """
    processor = ContentProcessor(links_file=links_file, output_dir=output_dir)
    await processor.process_content()

async def run_scraper(
    base_url: str,
    links_file: str,
    output_dir: str,
    max_pages: int = 10000,
    phase: str = "all"
):
    """Run the scraper in the specified phase.
    
    Args:
        base_url (str): Starting URL to collect links from
        links_file (str): Path to save/load links JSON file
        output_dir (str): Directory to save markdown files
        max_pages (int): Maximum number of pages to collect links from
        phase (str): Which phase to run ("collect", "process", or "all")
    """
    # if phase in ["collect", "all"]:
    #     logger.info("Starting link collection phase")
    #     await collect_links(
    #         base_url=base_url,
    #         output_file=links_file,
    #         max_pages=max_pages
    #     )
    
    # if phase in ["process", "all"]:
    logger.info("Starting content processing phase")
    await process_content(
        links_file=links_file,
        output_dir=output_dir,
    )

def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Nestle AI Chatbot Scraper")
    
    parser.add_argument(
        "--base-url",
        default="https://www.madewithnestle.ca/sitemap",
        help="Starting URL to collect links from"
    )
    
    parser.add_argument(
        "--links-file",
        default="../../../data/collected_links.json",
        help="Path to save/load links JSON file"
    )
    
    parser.add_argument(
        "--output-dir",
        default="../../../data/raw",
        help="Directory to save markdown files"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10000,
        help="Maximum number of pages to collect links from"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of URLs to process concurrently"
    )
    
    parser.add_argument(
        "--phase",
        choices=["collect", "process", "all"],
        default="all",
        help="Which phase to run"
    )
    
    args = parser.parse_args()
    
    # Create output directories
    os.makedirs(os.path.dirname(args.links_file), exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run scraper
    asyncio.run(run_scraper(
        base_url=args.base_url,
        links_file=args.links_file,
        output_dir=args.output_dir,
        max_pages=args.max_pages,
        phase=args.phase
    ))

if __name__ == "__main__":
    main() 