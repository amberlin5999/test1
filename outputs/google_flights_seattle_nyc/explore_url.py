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

        # Navigate to the flights search URL with the tfs parameter from the working search
        # This encodes: One way, Seattle -> New York, Aug 15, 2026
        tfs_url = (
            "https://www.google.com/travel/flights"
            "?tfs=CBwQARopEgoyMDI2LTA4LTE1agwIAxIIL20vMGQ5anJyDQgDEgkvbS8wMl8yODZAAUgBcAGCAQsI____________AZgBAg"
            "&tfu=KgIIAw"
        )
        await page.goto(tfs_url, wait_until="domcontentloaded")
        await asyncio.sleep(8)

        print(f"URL: {page.url[:400]}", flush=True)
        print(f"Title: {await page.title()}", flush=True)
        await page.screenshot(path=str(SCREENSHOTS / "expl_url_load.png"))

        # Get full body snapshot
        snapshot = await page.locator("body").aria_snapshot()
        lines = snapshot.split('\n')

        # Check if there's a "Done" button (calendar dialog)
        for i, line in enumerate(lines):
            if 'done' in line.lower() or 'calendar' in line.lower() or 'dialog' in line.lower():
                print(f"  L{i}: {line[:200]}", flush=True)
            if 'gridcell' in line.lower() and 'aug 15' in line.lower():
                print(f"  L{i}: {line[:300]}", flush=True)

        # Look for flight pricing buttons
        print("\n=== Flight-related content ===", flush=True)
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ['nonstop', '1 stop', '2 stop', 'stops', 'airline', 'flight', 'price']):
                if 'button' in line.lower() or 'text' in line.lower():
                    print(f"  L{i}: {line[:300]}", flush=True)

        # Print last 50 lines to see the end of the page
        print("\n=== Last 50 lines ===", flush=True)
        for line in lines[-50:]:
            print(line[:200], flush=True)

        await browser.close()

asyncio.run(main())
