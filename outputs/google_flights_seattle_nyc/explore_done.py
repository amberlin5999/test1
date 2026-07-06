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

        # Click "Done" to dismiss the calendar dialog
        done_btn = page.get_by_role("button", name="Done.")
        print(f"Done button: {await done_btn.count()}", flush=True)
        if await done_btn.count() > 0:
            await done_btn.click()
            await asyncio.sleep(3)
            print("Clicked Done", flush=True)
            await page.screenshot(path=str(SCREENSHOTS / "expl_done.png"))

        # Now see what's on the results page
        snapshot = await page.locator("body").aria_snapshot()
        
        # Check for flight listings after Done
        lines = snapshot.split('\n')
        print(f"\nTotal lines: {len(lines)}", flush=True)
        
        # Look for the price and flight list
        for i, line in enumerate(lines):
            if 'button' in line.lower() and any(kw in line.lower() for kw in ['nonstop', '1 stop', '2 stop', 'delta', 'alaska', 'american', 'united', 'jetblue', 'southwest', 'spirit', 'frontier']):
                print(f"  L{i}: {line[:300]}", flush=True)
        
        # Also check the bottom of the page for "View deal" or "Select" buttons
        for i, line in enumerate(lines[-100:]):
            actual_line = len(lines) - 100 + i
            if 'button' in line.lower() and ('usd' in line.lower() or '$' in line or 'nt$' in line.lower() or 'price' in line.lower()):
                print(f"  L{actual_line}: {line[:300]}", flush=True)

        # Print the main content region
        main_el = page.locator("main")
        if await main_el.count() > 0:
            main_snap = await main_el.aria_snapshot()
            print(f"\n=== Main content ({len(main_snap)} chars) ===", flush=True)
            print(main_snap[:5000], flush=True)

        await browser.close()

asyncio.run(main())
