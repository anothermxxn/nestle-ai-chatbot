import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Optional, Dict
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, Browser, Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class BrowserManager:
    """Async context manager for Playwright browser lifecycle management."""
    
    def __init__(self, headless: bool = False):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.headless = headless

    async def __aenter__(self) -> tuple[Browser, Page]:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        return self.browser, self.page

    async def __aexit__(self, exc_type, exc, tb):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

class LinkCollector:
    """Collects all links from a website and its subpages."""
    
    def __init__(self, base_url: str, output_file: str):
        """Initialize the link collector.
        
        Args:
            base_url (str): The starting URL to collect links from
            output_file (str): Path to save collected links
        """
        self.base_url = base_url
        self.output_file = output_file
        self.visited: Set[str] = set()
        self.to_visit: Set[str] = {base_url}
        self.collected_data: Dict[str, Dict] = {}
        
        # Parse base domain for filtering
        parsed = urlparse(base_url)
        self.base_domain = parsed.netloc
    
    def _cleanup_url(self, url: str) -> str:
        """Basic URL cleanup without normalization."""
        # Remove fragment as it doesn't affect content
        return url.split("#")[0]
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to base domain."""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == self.base_domain
                and parsed.scheme in ("http", "https")
                and not any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".pdf"])
            )
        except Exception:
            return False
    
    async def _extract_page_info(self, page: Page) -> Dict:
        """Extract page title and metadata."""
        title = await page.title()
        
        # Try to get meta description
        description = await page.evaluate("""
            () => {
                const meta = document.querySelector('meta[name="description"]');
                return meta ? meta.getAttribute("content") : "";
            }
        """)
        
        return {
            "title": title,
            "description": description,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    async def _extract_links(self, page: Page) -> Set[str]:
        """Extract all links from the page."""
        links = set()
        
        # Get all anchor tags
        anchors = await page.query_selector_all("a")
        for anchor in anchors:
            try:
                href = await anchor.get_attribute("href")
                if href:
                    absolute_url = urljoin(self.base_url, href)
                    clean_url = self._cleanup_url(absolute_url)
                    if self._is_valid_url(clean_url):
                        links.add(clean_url)
            except Exception as e:
                logger.debug(f"Error extracting link: {e}")
                continue
        
        return links
    
    async def collect_links(self, max_pages: int = 1000, concurrency: int = 5):
        """Collect links from the website and its subpages.
        
        Args:
            max_pages (int): Maximum number of pages to process
            concurrency (int): Number of concurrent browser pages
        """
        async with BrowserManager() as (browser, _):
            # Create a pool of pages
            pages = []
            for _ in range(concurrency):
                page = await browser.new_page()
                pages.append(page)
            
            try:
                while self.to_visit and len(self.visited) < max_pages:
                    # Process up to concurrency pages at once
                    current_batch = list(self.to_visit)[:concurrency]
                    self.to_visit -= set(current_batch)
                    
                    tasks = []
                    for url, page in zip(current_batch, pages):
                        if url in self.visited:
                            continue
                        
                        logger.info(f"Collecting links from: {url}")
                        tasks.append(self._process_page(url, page))
                    
                    if tasks:
                        await asyncio.gather(*tasks)
                    
                    # Break if no more URLs to process
                    if not self.to_visit:
                        break
                
            finally:
                # Close all pages
                for page in pages:
                    await page.close()
        
        # Save collected data
        self._save_data()
        
        logger.info(f"Link collection complete. Processed {len(self.visited)} pages.")
    
    async def _process_page(self, url: str, page: Page):
        """Process a single page to extract links and metadata."""
        try:
            await page.goto(url, wait_until="networkidle")
            
            # Extract page info and links
            page_info = await self._extract_page_info(page)
            links = await self._extract_links(page)
            
            # Store data
            self.collected_data[url] = {
                "info": page_info,
                "outgoing_links": list(links)
            }
            
            # Update tracking sets
            self.visited.add(url)
            self.to_visit.update(links - self.visited)
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            # Add to visited to avoid retrying
            self.visited.add(url)
    
    def _save_data(self):
        """Save collected data to JSON file."""
        output = {
            "metadata": {
                "base_url": self.base_url,
                "total_pages": len(self.visited),
                "timestamp": datetime.utcnow().isoformat()
            },
            "pages": self.collected_data
        }
        
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved collected data to {self.output_file}") 