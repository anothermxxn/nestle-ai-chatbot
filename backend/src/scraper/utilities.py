import asyncio
import functools
import logging
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Callable, Any, Coroutine, Optional

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

    async def __aexit__(self):
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
async def scrape_text(url: str, page: Optional[Page] = None) -> List[Dict[str, str]]:
    """
    Scrape and group visible text content by headings from a web page.
    
    Args:
        url (str): The URL of the page to scrape.
        page (Page, optional): Playwright Page instance to use.
    Returns:
        List[Dict[str, str]]: List of sections with "heading" and "content".
    """
    if page is None:
        async with BrowserManager() as (_, page):
            return await scrape_text(url, page)
    logger.info(f"Navigating to {url}")
    await page.goto(url)
    await page.wait_for_load_state("networkidle")

    # Get all elements in the body
    all_elements = await page.query_selector_all("body *")
    # Get all headings and their indices
    headings = []
    for idx, el in enumerate(all_elements):
        tag = await el.get_property("tagName")
        tag = (await tag.json_value()).lower()
        if tag in [f"h{i}" for i in range(1, 7)]:
            text = (await el.inner_text()).strip()
            if text:
                headings.append((idx, tag, text))
    # Group content under each heading
    sections = []
    for i, (start_idx, tag, heading_text) in enumerate(headings):
        end_idx = headings[i+1][0] if i+1 < len(headings) else len(all_elements)
        content_lines = []
        for el in all_elements[start_idx+1:end_idx]:
            try:
                text = (await el.inner_text()).strip()
                if text:
                    content_lines.append(text)
            except Exception as e:
                logger.debug(f"Error extracting text from element: {e}")
                continue
        content = "\n".join(content_lines).strip()
        if heading_text and content:
            sections.append({"heading": heading_text, "content": content})
                
    logger.info(f"Scraped {len(sections)} text sections from {url}")
    return sections

@async_retry()
async def scrape_images(url: str, page: Optional[Page] = None) -> List[str]:
    """
    Scrape all image URLs from a web page.
    
    Args:
        url (str): The URL of the page to scrape.
        page (Page, optional): Playwright Page instance to use.
    Returns:
        List[str]: List of image URLs.
    """
    if page is None:
        async with BrowserManager() as (_, page):
            return await scrape_images(url, page)
    logger.info(f"Navigating to {url}")
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    # Select all <img> elements
    img_elements = await page.query_selector_all("img")
    image_urls = []
    for img in img_elements:
        src = await img.get_attribute("src")
        if src:
            image_urls.append(src)
                
    logger.info(f"Scraped {len(image_urls)} images from {url}")
    return image_urls

@async_retry()
async def scrape_links(url: str, page: Optional[Page] = None) -> List[str]:
    """
    Scrape all unique links from a web page.
    
    Args:
        url (str): The URL of the page to scrape.
        page (Page, optional): Playwright Page instance to use.
    Returns:
        List[str]: List of unique hrefs.
    """
    if page is None:
        async with BrowserManager() as (_, page):
            return await scrape_links(url, page)
    logger.info(f"Navigating to {url}")
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    # Select all <a> elements
    a_elements = await page.query_selector_all("a")
    links = set()
    for a in a_elements:
        href = await a.get_attribute("href")
        if href and href.strip():
            links.add(href.strip())
                
    logger.info(f"Scraped {len(links)} links from {url}")
    return list(links)

@async_retry()
async def scrape_tables(url: str, page: Optional[Page] = None) -> List[Dict[str, List]]:
    """
    Scrape all tables from a web page, extracting headers and rows.
    
    Args:
        url (str): The URL of the page to scrape.
        page (Page, optional): Playwright Page instance to use.
    Returns:
        List[Dict[str, List]]: List of tables, each with "headers" and "rows".
    """
    if page is None:
        async with BrowserManager() as (_, page):
            return await scrape_tables(url, page)
    logger.info(f"Navigating to {url}")
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    
    tables = await page.query_selector_all("table")
    result = []
    for table in tables:
        headers = []
        rows = []
        # Try to get headers from <th> or first <tr>
        header_row = await table.query_selector("tr")
        if header_row:
            ths = await header_row.query_selector_all("th")
            if ths:
                headers = [ (await th.inner_text()).strip() for th in ths ]
            else:
                tds = await header_row.query_selector_all("td")
                headers = [ (await td.inner_text()).strip() for td in tds ]
        # Get all rows (skip header row)
        all_rows = await table.query_selector_all("tr")
        for i, row in enumerate(all_rows):
            # Skip header row
            if i == 0:
                continue
            cells = await row.query_selector_all("td")
            row_data = [ (await cell.inner_text()).strip() for cell in cells ]
            if row_data:
                rows.append(row_data)
        if headers or rows:
            result.append({"headers": headers, "rows": rows})
                
    logger.info(f"Scraped {len(result)} tables from {url}")
    return result

# if __name__ == "__main__":
#     url = "https://www.madewithnestle.ca/"

#     text = asyncio.run(scrape_text(url))
#     for section in text:
#         print(f"\n=== {section['heading']} ===\n{section['content'][:500]}")

#     images = asyncio.run(scrape_images(url))
#     for img_url in images[:10]:
#         print(img_url)

#     links = asyncio.run(scrape_links(url))
#     for link in links[:10]:
#         print(link)

#     tables = asyncio.run(scrape_tables(url))
#     for table in tables:
#         print("\nTable:")
#         print("Headers:", table["headers"])
#         for row in table["rows"][:5]:
#             print("Row:", row)
    
#     logging.shutdown()