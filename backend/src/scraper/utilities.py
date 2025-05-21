import asyncio
import functools
import logging
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Callable, Any, Coroutine, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


log_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logging.basicConfig(
    filename=f"../../../logs/scraper_{log_time}.log",
    level=logging.INFO,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Async context manager for Playwright browser lifecycle.
    """
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        return self.browser, self.page

    async def __aexit__(self, exc_type, exc, tb):
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


def async_retry(max_attempts: int = 3, delay: int = 5):
    """
    Decorator for retrying an async function on exception.
    
    Args:
        max_attempts (int): Maximum number of attempts.
        delay (int): Delay in seconds between attempts.
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Attempt {attempt} for {func.__name__}")
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}: {exc}")
                    if attempt < max_attempts:
                        logger.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}.")
                        raise last_exc
        return wrapper
    return decorator

@async_retry()
async def scrape_content(url: str, page: Optional[Page] = None) -> List[Dict[str, Any]]:
    """
    Scrape text, images, links, and tables grouped by heading/theme from a web page.
    
    Args:
        url (str): The URL of the page to scrape.
        page (Page, optional): Playwright Page instance to use. If None, a new browser/page will be created.
    
    Returns:
        List[Dict[str, Any]]: List of sections, each with keys:
            - 'heading': The section heading (str)
            - 'content': The grouped text content under the heading (str)
            - 'images': List of image URLs (List[str])
            - 'links': List of link hrefs (List[str])
            - 'tables': List of tables, each as a dict with 'headers' and 'rows'
    """
    close_page = False
    
    if page is None:
        close_page = True
        async with BrowserManager() as (_, page):
            return await scrape_content(url, page)
        
    logger.info(f"Navigating to {url}")
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    all_elements = await page.query_selector_all("body *")

    headings = []
    for idx, el in enumerate(all_elements):
        tag = await el.get_property("tagName")
        tag = (await tag.json_value()).lower()
        if tag in [f"h{i}" for i in range(1, 7)]:
            text = (await el.inner_text()).strip()
            if text:
                headings.append((idx, tag, text))
                
    sections = []
    for i, (start_idx, tag, heading_text) in enumerate(headings):
        end_idx = headings[i+1][0] if i+1 < len(headings) else len(all_elements)
        content_lines = []
        images = []
        links = []
        tables = []
        
        for el in all_elements[start_idx+1:end_idx]:
            el_tag = await el.get_property("tagName")
            el_tag = (await el_tag.json_value()).lower()
            
            try:
                # Text
                if el_tag not in [f"h{i}" for i in range(1, 7)] and el_tag not in ["img", "a", "table"]:
                    text = (await el.inner_text()).strip()
                    if text:
                        content_lines.append(text)
                # Images
                if el_tag == "img":
                    src = await el.get_attribute("src")
                    if src:
                        images.append(src)
                # Links
                if el_tag == "a":
                    href = await el.get_attribute("href")
                    if href:
                        links.append(href)
                # Tables
                if el_tag == "table":
                    header_row = await el.query_selector("tr")
                    table_headers = []
                    table_rows = []
                    
                    if header_row:
                        ths = await header_row.query_selector_all("th")
                        if ths:
                            table_headers = [ (await th.inner_text()).strip() for th in ths ]
                        else:
                            tds = await header_row.query_selector_all("td")
                            table_headers = [ (await td.inner_text()).strip() for td in tds ]
                    
                    all_rows = await el.query_selector_all("tr")
                    for j, row in enumerate(all_rows):
                        if j == 0:
                            continue
                        cells = await row.query_selector_all("td")
                        row_data = [ (await cell.inner_text()).strip() for cell in cells ]
                        if row_data:
                            table_rows.append(row_data)
                            
                    if table_headers or table_rows:
                        tables.append({"headers": table_headers, "rows": table_rows})
            except Exception as e:
                logger.debug(f"Error extracting element: {e}")
                continue
               
        section = {
            "heading": heading_text,
            "content": "\n".join(content_lines).strip(),
            "images": images,
            "links": links,
            "tables": tables
        }
        sections.append(section)
        
    logger.info(f"Scraped {len(sections)} sections from {url}")
    if close_page:
        await page.close()
    return sections

async def scrape_content_crawl4ai(url: str):
    """
    Scrape content from a web page using Crawl4AI.
    
    Args:
        url (str): The URL of the page to scrape.
    
    """
    browser_config = BrowserConfig(
        headless=True,  
        verbose=True,
    )
    run_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
        ),
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )
        return result