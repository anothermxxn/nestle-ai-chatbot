import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Set
from urllib.parse import urlparse, urljoin
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ContentProcessor:
    """Processes collected links using crawl4ai to generate markdown content."""
    
    def __init__(self, links_file: str, output_dir: str):
        """Initialize the content processor.
        
        Args:
            links_file (str): Path to the JSON file containing collected links
            output_dir (str): Directory to save markdown files
        """
        self.links_file = links_file
        self.output_dir = output_dir
        self.processed_urls: Dict[str, Dict] = {}
        self.to_process: Set[str] = set()  # URLs waiting to be processed
        self.base_domain = ""  # Will be set when loading URLs
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to base domain and is not a media file or filter URL."""
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc == self.base_domain
                and parsed.scheme in ("http", "https")
                and "recipe_tags_filter" not in url
                and not any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".pdf"])
            )
        except Exception:
            return False
    
    def _load_urls(self) -> List[str]:
        """Load URLs from file and remove exact duplicates."""
        with open(self.links_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Filter out recipe_tags_filter URLs first
            urls = [url for url in data["pages"].keys() if "recipe_tags_filter" not in url]
            
            # Set base domain from first URL
            if urls:
                self.base_domain = urlparse(urls[0]).netloc
        
        # Remove exact duplicates while preserving order
        unique_urls = []
        seen = set()
        
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
                self.to_process.add(url)
            else:
                logger.info(f"Found exact duplicate URL: {url}")
        
        logger.info(f"Loaded {len(unique_urls)} unique URLs from {len(urls)} total URLs")
        return unique_urls
    
    async def _extract_links(self, page_content: str, base_url: str) -> Set[str]:
        """Extract links from page content."""
        links = set()
        
        # Use a simple regex to find links (crawl4ai's content is markdown)
        import re
        href_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        matches = href_pattern.findall(page_content)
        
        for _, href in matches:
            try:
                absolute_url = urljoin(base_url, href)
                if self._is_valid_url(absolute_url):
                    if absolute_url not in self.to_process and absolute_url not in self.processed_urls:
                        self.to_process.add(absolute_url)
                        links.add(absolute_url)
            except Exception as e:
                logger.debug(f"Error processing link {href}: {e}")
        
        return links
    
    def _get_output_path(self, url: str) -> str:
        """Generate output file path for a URL.
        
        Example:
            URL: https://www.madewithnestle.ca/recipe/cardamom-donuts-vanilla-bean-ice-cream/1
            Filename: recipe_cardamom-donuts-vanilla-bean-ice-cream_1.md
        """
        try:
            # Remove domain part
            path = url.split(self.base_domain)[-1].strip("/")
            
            # Split path into parts
            parts = [part for part in path.split("/") if part]
            
            # Join parts with underscores
            filename = "_".join(parts)
            
            # Handle empty or invalid paths
            if not filename:
                # Fallback to safe version of full URL
                filename = url.replace("://", "_").replace("/", "_").replace(".", "_")
            
            return os.path.join(self.output_dir, f"{filename}.md")
            
        except Exception as e:
            logger.error(f"Error creating filename for {url}: {e}")
            # Fallback to safe version of full URL
            safe_name = url.replace("://", "_").replace("/", "_").replace(".", "_")
            return os.path.join(self.output_dir, f"{safe_name}.md")
    
    async def process_content(self, max_retries: int = 3):
        """Process URLs sequentially, following links to subpages."""
        urls = self._load_urls()
        
        logger.info(f"Starting content processing with {len(self.to_process)} initial URLs")
        
        # Configure crawl4ai
        browser_config = BrowserConfig(
            headless=True,
            verbose=True
        )
        
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48,
                    threshold_type="fixed",
                    min_word_threshold=0
                )
            )
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            while self.to_process:
                url = self.to_process.pop()
                
                # Skip if already processed
                if url in self.processed_urls and self.processed_urls[url]["success"]:
                    continue
                
                logger.info(f"Processing {url}")
                output_path = self._get_output_path(url)
                
                try:
                    for attempt in range(max_retries):
                        try:
                            result = await crawler.arun(url=url, config=run_config)
                            
                            if result.success:
                                content = result.markdown.fit_markdown
                                
                                # Save content
                                with open(output_path, "w", encoding="utf-8") as f:
                                    f.write(content)
                                
                                self.processed_urls[url] = {
                                    "success": True,
                                    "output_path": output_path,
                                    "processed_at": datetime.utcnow().isoformat()
                                }
                                
                                # Extract and add new links to process
                                new_links = await self._extract_links(content, url)
                                if new_links:
                                    logger.info(f"Found {len(new_links)} new links in {url}")
                                
                                break
                            
                        except Exception as e:
                            logger.error(f"Error processing {url} (attempt {attempt + 1}): {str(e)}")
                            if attempt == max_retries - 1:
                                self.processed_urls[url] = {
                                    "success": False,
                                    "error": str(e),
                                    "processed_at": datetime.utcnow().isoformat()
                                }
                
                except Exception as e:
                    logger.error(f"Unhandled error processing {url}: {str(e)}")
                    self.processed_urls[url] = {
                        "success": False,
                        "error": str(e),
                        "processed_at": datetime.utcnow().isoformat()
                    }
        
        # Save processing results
        self._save_results()
        
        logger.info("Content processing complete")
        logger.info(f"Processed {len(self.processed_urls)} URLs in total")
    
    def _save_results(self):
        """Save processing results to JSON file."""
        results = {
            "metadata": {
                "total_urls": len(self.processed_urls),
                "successful": sum(1 for v in self.processed_urls.values() if v["success"]),
                "timestamp": datetime.utcnow().isoformat()
            },
            "results": self.processed_urls
        }
        
        results_path = os.path.join(self.output_dir, "processing_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved processing results to {results_path}") 