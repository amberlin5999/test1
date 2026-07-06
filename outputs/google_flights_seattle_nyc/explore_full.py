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

        # Step 1: One way
        print("=== Step 1: One way ===", flush=True)
        await page.get_by_role("combobox").filter(has_text="Round trip").first.click()
        await asyncio.sleep(1)
        await page.get_by_role("option", name="One way").first.click()
        await asyncio.sleep(3)

        # Step 2: Origin - Seattle
        print("=== Step 2: Origin ===", flush=True)
        await page.locator("input[aria-label='Where from?']").first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("Seattle", delay=60)
        await asyncio.sleep(2)
        # Click "Seattle, Washington, USA" (first geographic option)
        await page.locator("[role='option']").nth(7).click()
        await asyncio.sleep(1)
        print(f"Origin: '{await page.locator('input[aria-label=\"Where from?\"]').first.input_value()}'", flush=True)

        # Step 3: Destination - New York
        print("=== Step 3: Dest ===", flush=True)
        await page.locator("input[aria-label='Where to? ']").first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("New York", delay=60)
        await asyncio.sleep(2)
        # Print options
        for i in range(min(await page.locator("[role='option']").count(), 15)):
            txt = await page.locator("[role='option']").nth(i).text_content()
            print(f"  {i}: {(txt or '')[:80]}", flush=True)
        # Click "New York, USA" (city option, index 7-8)
        await page.locator("[role='option']").filter(has_text=re.compile(r"^New York, USA", re.IGNORECASE)).first.click()
        await asyncio.sleep(1)
        print(f"Dest: '{await page.locator('input[aria-label=\"Where to? \"]').first.input_value()}'", flush=True)

        # Step 4: Departure date
        print("=== Step 4: Date ===", flush=True)
        dep = page.locator("input[aria-label='Departure']").first
        await dep.click()
        await asyncio.sleep(0.5)
        await dep.fill("")
        await dep.type("Aug 15, 2026", delay=30)
        await asyncio.sleep(1)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)
        print(f"Date: '{await dep.input_value()}'", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "expl_form_filled.png"))

        # Step 5: Search - press Enter to submit
        print("=== Step 5: Search ===", flush=True)
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)
        await page.screenshot(path=str(SCREENSHOTS / "expl_search_results.png"))
        print(f"URL: {page.url[:400]}", flush=True)
        print(f"Title: {await page.title()}", flush=True)

        # Get the full page snapshot
        snapshot = await page.locator("body").aria_snapshot()
        # Look for prices
        lines = snapshot.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ['price', 'cheapest', 'total', 'fare', 'usd', '$', 'from']):
                print(f"  L{i}: {line[:200]}", flush=True)

        # Extract all flight-related text
        main_content = await page.locator("main").aria_snapshot() if await page.locator("main").count() > 0 else ""
        print(f"\n=== Main content ({len(main_content)} chars) ===", flush=True)
        print(main_content[:10000], flush=True)

        await browser.close()

asyncio.run(main())
