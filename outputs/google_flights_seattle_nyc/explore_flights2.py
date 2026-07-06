import asyncio, os, re
from pathlib import Path
from playwright.async_api import async_playwright

WORKSPACE = Path(os.environ["WORKSPACE_DIR"])
SCREENSHOTS = WORKSPACE / "screenshots"

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # One way
        await page.get_by_role("combobox").filter(has_text="Round trip").first.click()
        await asyncio.sleep(1)
        await page.get_by_role("option", name="One way").first.click()
        await asyncio.sleep(3)

        # Origin
        await page.locator("input[aria-label='Where from?']").first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("Seattle", delay=60)
        await asyncio.sleep(2)
        await page.locator("[role='option']").nth(7).click()
        await asyncio.sleep(1)

        # Dest
        await page.locator("input[aria-label='Where to? ']").first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("New York", delay=60)
        await asyncio.sleep(2)
        await page.locator("[role='option']").filter(has_text=re.compile(r"^New York, USA", re.IGNORECASE)).first.click()
        await asyncio.sleep(1)

        # Date
        await page.locator("input[aria-label='Departure']").first.click()
        await asyncio.sleep(0.5)
        await page.locator("input[aria-label='Departure']").first.fill("")
        await page.locator("input[aria-label='Departure']").first.type("Aug 15, 2026", delay=30)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        # Search - press Enter
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(8)

        # Print FULL aria snapshot
        snapshot = await page.locator("body").aria_snapshot()
        print(snapshot, flush=True)

        await browser.close()

asyncio.run(main())
