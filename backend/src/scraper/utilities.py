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
