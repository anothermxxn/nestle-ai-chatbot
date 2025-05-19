import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict

async def scrape_text(url: str) -> List[Dict[str, str]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        # Get all elements in the body
        all_elements = await page.query_selector_all('body *')
        # Get all headings and their indices
        headings = []
        for idx, el in enumerate(all_elements):
            tag = await el.get_property('tagName')
            tag = (await tag.json_value()).lower()
            if tag in [f'h{i}' for i in range(1, 7)]:
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
                except Exception:
                    continue
            content = '\n'.join(content_lines).strip()
            if heading_text and content:
                sections.append({"heading": heading_text, "content": content})
                
        await browser.close()
        return sections

async def scrape_images(url: str) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Select all <img> elements
        img_elements = await page.query_selector_all('img')
        image_urls = []
        for img in img_elements:
            src = await img.get_attribute('src')
            if src:
                image_urls.append(src)
                
        await browser.close()
        return image_urls

async def scrape_links(url: str) -> List[str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        # Select all <a> elements
        a_elements = await page.query_selector_all('a')
        links = set()
        for a in a_elements:
            href = await a.get_attribute('href')
            if href and href.strip():
                links.add(href.strip())
                
        await browser.close()
        return list(links)

# TODO: Need to test
async def scrape_tables(url: str) -> List[Dict[str, List]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        tables = await page.query_selector_all('table')
        result = []
        for table in tables:
            headers = []
            rows = []
            # Try to get headers from <th> or first <tr>
            header_row = await table.query_selector('tr')
            if header_row:
                ths = await header_row.query_selector_all('th')
                if ths:
                    headers = [ (await th.inner_text()).strip() for th in ths ]
                else:
                    tds = await header_row.query_selector_all('td')
                    headers = [ (await td.inner_text()).strip() for td in tds ]
            # Get all rows (skip header row)
            all_rows = await table.query_selector_all('tr')
            for i, row in enumerate(all_rows):
                # Skip header row
                if i == 0:
                    continue
                cells = await row.query_selector_all('td')
                row_data = [ (await cell.inner_text()).strip() for cell in cells ]
                if row_data:
                    rows.append(row_data)
            if headers or rows:
                result.append({'headers': headers, 'rows': rows})
        await browser.close()
        return result

# if __name__ == "__main__":
#     url = "https://www.nestle.com/investors/overview"

    # text = asyncio.run(scrape_text(url))
    # for section in text:
    #     print(f"\n=== {section['heading']} ===\n{section['content'][:500]}")

    # images = asyncio.run(scrape_images(url))
    # for img_url in images[:10]:
    #     print(img_url)

    # links = asyncio.run(scrape_links(url))
    # for link in links[:10]:
    #     print(link)

    # tables = asyncio.run(scrape_tables(url))
    # for table in tables:
    #     print("\nTable:")
    #     print("Headers:", table['headers'])
    #     for row in table['rows'][:5]:
    #         print("Row:", row)
 