import asyncio, os, sys
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE = Path(os.environ["WORKSPACE_DIR"])
SCREENSHOTS = WORKSPACE / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)

async def main():
    print("Starting...", flush=True)
    async with async_playwright() as playwright:
        print("Playwright started", flush=True)
        browser = await playwright.firefox.launch(headless=True)
        print("Browser launched", flush=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()
        print("Navigating...", flush=True)
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        print("Page loaded", flush=True)
        await asyncio.sleep(5)
        print("URL:", page.url, flush=True)
        print("TITLE:", await page.title(), flush=True)
        await page.screenshot(path=str(SCREENSHOTS / "explore_1_homepage.png"))
        print("Screenshot saved", flush=True)
        snapshot = await page.locator("body").aria_snapshot()
        print("ARIA_SNAPSHOT:")
        print(snapshot[:15000], flush=True)
        await browser.close()

asyncio.run(main())
