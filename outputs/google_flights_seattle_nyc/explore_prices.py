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

        # Origin - Seattle
        await page.locator("input[aria-label='Where from?']").first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("Seattle", delay=60)
        await asyncio.sleep(2)
        await page.locator("[role='option']").nth(7).click()
        await asyncio.sleep(1)

        # Dest - New York
        await page.locator("input[aria-label='Where to? ']").first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("New York", delay=60)
        await asyncio.sleep(2)
        await page.locator("[role='option']").filter(has_text=re.compile(r"^New York, USA", re.IGNORECASE)).first.click()
        await asyncio.sleep(1)

        # Date - Aug 15
        await page.locator("input[aria-label='Departure']").first.click()
        await asyncio.sleep(0.5)
        await page.locator("input[aria-label='Departure']").first.fill("")
        await page.locator("input[aria-label='Departure']").first.type("Aug 15, 2026", delay=30)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        # Search - press Enter
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)

        print(f"URL: {page.url[:400]}", flush=True)

        # Check the search form in results
        search_form = await page.locator("[role='search']").aria_snapshot()
        print(f"\n=== Search form ===", flush=True)
        print(search_form[:2000], flush=True)

        # Click on "Aug 15" in the date grid to see actual flights
        # First, let's find the Aug 15 button and click it to see flight details
        aug15_btn = page.locator("[role='grid']").locator("button").filter(has_text=re.compile(r"Aug 15", re.IGNORECASE))
        print(f"\nAug 15 button count: {await aug15_btn.count()}", flush=True)
        
        if await aug15_btn.count() > 0:
            # Click the Aug 15 date chip/button
            await aug15_btn.first.click()
            await asyncio.sleep(3)
            await page.screenshot(path=str(SCREENSHOTS / "expl_aug15_flights.png"))
            print("Clicked Aug 15", flush=True)

        # Get the main content area
        snapshot = await page.locator("body").aria_snapshot()
        
        # Find flight-related content for Aug 15
        lines = snapshot.split('\n')
        in_flight_list = False
        for i, line in enumerate(lines):
            if 'aug 15' in line.lower() or 'august 15' in line.lower():
                print(f"  L{i}: {line[:250]}", flush=True)
            if any(kw in line.lower() for kw in ['price', 'cheapest', 'sort', 'filter', 'result', 'flight']):
                print(f"  L{i}: {line[:200]}", flush=True)

        # Print full snapshot to find flight listings
        print(f"\n\n=== Full snapshot key sections ===", flush=True)
        # Look for buttons that contain "$" or "NT$" or "TWD" or "dollars"
        for i, line in enumerate(lines):
            if ('$' in line or 'NT$' in line or 'TW$' in line) and 'button' in line.lower():
                print(f"  L{i}: {line[:250]}", flush=True)

        await browser.close()

asyncio.run(main())
