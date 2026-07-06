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

        # Use deep link with route pre-filled
        tfs_url = (
            "https://www.google.com/travel/flights"
            "?tfs=CBwQARopEgoyMDI2LTA4LTE1agwIAxIIL20vMGQ5anJyDQgDEgkvbS8wMl8yODZAAUgBcAGCAQsI____________AZgBAg"
            "&tfu=KgIIAw"
        )
        await page.goto(tfs_url, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        print(f"Title: {await page.title()}", flush=True)

        # Check the form - see if origin/dest are pre-filled
        snapshot = await page.locator("[role='search']").aria_snapshot()
        print(f"Search form:\n{snapshot[:2000]}", flush=True)

        # Try clicking the departure field and setting the date
        dep = page.locator("input[aria-label='Departure']")
        print(f"Dep count: {await dep.count()}", flush=True)
        if await dep.count() > 0:
            await dep.first.click()
            await asyncio.sleep(1)
            # The calendar dialog might appear
            await dep.first.fill("")
            await dep.first.type("Aug 15, 2026", delay=40)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)
            
            # Check if there's a Done button
            done = page.get_by_role("button", name="Done.")
            if await done.count() > 0:
                await done.click()
                await asyncio.sleep(2)
                print("Clicked Done", flush=True)

            # Now click "Search for flights" 
            search_btn = page.get_by_role("button", name="Search for flights")
            print(f"Search btn: {await search_btn.count()}", flush=True)
            if await search_btn.count() > 0:
                await search_btn.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(5)
                print(f"After search URL: {page.url[:400]}", flush=True)
                await page.screenshot(path=str(SCREENSHOTS / "expl_search_result.png"))

                # Get the results
                snapshot = await page.locator("body").aria_snapshot()
                lines = snapshot.split('\n')
                print(f"\nTotal lines: {len(lines)}", flush=True)

                # Extract flight info
                for i, line in enumerate(lines):
                    if any(kw in line.lower() for kw in ['nonstop', 'stop', 'airline', 'flight']) and ('button' in line.lower() or 'link' in line.lower()):
                        if any(currency in line for currency in ['$', 'NT$', 'TWD', 'dollars']):
                            print(f"  L{i}: {line[:300]}", flush=True)
                
                # Also search for any content after the date grid
                print("\n=== Bottom 80 lines ===", flush=True)
                for line in lines[-80:]:
                    print(line[:200], flush=True)

        await browser.close()

asyncio.run(main())
