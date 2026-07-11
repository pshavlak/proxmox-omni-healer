import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # Launching browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        print(f"Page title: {await page.title()}")
        # Keep open for a moment to demonstrate
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
