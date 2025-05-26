import logging

from utils.import_helper import setup_imports
setup_imports(__file__)
from .link_collector import LinkCollector
from .content_processor import ContentProcessor
from config import MAX_PAGES_LARGE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def collect_links(base_url: str, output_file: str, max_pages: int = None):
    """Collect links from the website and save to file.
    
    Args:
        base_url (str): Starting URL to collect links from
        output_file (str): Path to save collected links
        max_pages (int): Maximum number of pages to process
    """
    max_pages = max_pages or MAX_PAGES_LARGE
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
    max_pages: int = None,
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
    if phase in ["collect", "all"]:
        logger.info("Starting link collection phase")
        await collect_links(
            base_url=base_url,
            output_file=links_file,
            max_pages=max_pages
        )
    
    if phase in ["process", "all"]:
        logger.info("Starting content processing phase")
        await process_content(
            links_file=links_file,
            output_dir=output_dir,
        ) 