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

        # Search
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)

        # Find and click the Aug 15 date button in the grid
        # Try various selectors
        aug15 = page.locator("button").filter(has_text=re.compile(r"15.*5,710|15.*5,712|Aug 15", re.IGNORECASE))
        print(f"Aug 15 via price: {await aug15.count()}", flush=True)
        
        # Try by gridcell 
        aug15_cell = page.locator("[role='gridcell']").filter(has_text=re.compile(r"Aug 15", re.IGNORECASE))
        print(f"Aug 15 cell: {await aug15_cell.count()}", flush=True)
        
        # Try the selected gridcell
        aug15_sel = page.locator("[role='gridcell'][aria-selected='true']")
        print(f"Selected cell: {await aug15_sel.count()}", flush=True)
        if await aug15_sel.count() > 0:
            print(f"  text: {(await aug15_sel.first.text_content() or '')[:100]}", flush=True)
            await aug15_sel.first.click()
            await asyncio.sleep(3)
            print("Clicked selected cell", flush=True)
            await page.screenshot(path=str(SCREENSHOTS / "expl_flights_list.png"))

        # Get the full body snapshot after clicking
        snapshot = await page.locator("body").aria_snapshot()
        lines = snapshot.split('\n')
        
        # Find flight list items
        for i, line in enumerate(lines):
            txt = line.lower()
            if any(kw in txt for kw in ['nonstop', 'stop', 'airline', 'airways', 'air ', 'flight', 'depart', 'arrive', 'hr ', 'hour', 'min']):
                if 'button' in txt and ('$' in line or 'twd' in txt or 'nt$' in txt):
                    print(f"  L{i}: {line[:250]}", flush=True)

        # Also look for the price list
        print("\n=== All buttons with prices ===", flush=True)
        for i, line in enumerate(lines):
            if ('$' in line or 'NT$' in line) and 'button' in line.lower() and ('aug 15' in line.lower() or 'seatle' in line.lower() or 'new york' in line.lower() or 'nonstop' in line.lower() or 'stop' in line.lower()):
                print(f"  L{i}: {line[:250]}", flush=True)

        await browser.close()

asyncio.run(main())
