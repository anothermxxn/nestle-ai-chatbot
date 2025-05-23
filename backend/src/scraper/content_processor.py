import os
import json
import logging
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse
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
        self.base_domain = ""
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def _load_urls(self) -> List[str]:
        """Load URLs from the collected_links.json file."""
        with open(self.links_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            urls = list(data["pages"].keys())
            
            # Set base domain from first URL
            if urls:
                self.base_domain = urlparse(urls[0]).netloc
        
        logger.info(f"Loaded {len(urls)} URLs to process from {self.links_file}")
        return urls
    
    def _get_output_path(self, url: str) -> str:
        """Generate output file path for a URL."""
        try:
            # Remove domain part
            path = url.split(self.base_domain)[-1].strip("/")
            
            # Split path into parts and join with underscores
            parts = [part for part in path.split("/") if part]
            filename = "_".join(parts)
            
            # Handle empty or invalid paths
            if not filename:
                filename = url.replace("://", "_").replace("/", "_").replace(".", "_")
            
            return os.path.join(self.output_dir, f"{filename}.md")
            
        except Exception as e:
            logger.error(f"Error creating filename for {url}: {e}")
            safe_name = url.replace("://", "_").replace("/", "_").replace(".", "_")
            return os.path.join(self.output_dir, f"{safe_name}.md")
    
    async def process_content(self, max_retries: int = 3):
        """Process all collected URLs to generate markdown content."""
        urls = self._load_urls()
        
        logger.info(f"Starting content processing for {len(urls)} URLs")
        
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
            for i, url in enumerate(urls, 1):
                logger.info(f"Processing {i}/{len(urls)}: {url}")
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
                                
                                logger.info(f"Successfully processed: {url}")
                                break
                            else:
                                logger.warning(f"Failed to crawl {url}: {result.error_message}")
                                if attempt == max_retries - 1:
                                    self.processed_urls[url] = {
                                        "success": False,
                                        "error": result.error_message or "Unknown crawling error",
                                        "processed_at": datetime.utcnow().isoformat()
                                    }
                            
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
        
        successful = sum(1 for v in self.processed_urls.values() if v["success"])
        logger.info(f"Content processing complete: {successful}/{len(urls)} URLs processed successfully")
    
    def _save_results(self):
        """Save processing results to JSON file."""
        successful = sum(1 for v in self.processed_urls.values() if v["success"])
        results = {
            "metadata": {
                "total_urls": len(self.processed_urls),
                "successful": successful,
                "failed": len(self.processed_urls) - successful,
                "timestamp": datetime.utcnow().isoformat()
            },
            "results": self.processed_urls
        }
        
        results_path = os.path.join(self.output_dir, "processing_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved processing results to {results_path}") 