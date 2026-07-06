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
        # Click the origin field to open the autocomplete
        origin = page.locator("input[aria-label='Where from?']")
        await origin.first.click()
        await asyncio.sleep(1)
        await page.screenshot(path=str(SCREENSHOTS / "expl_origin_clicked.png"))

        # Now the "Where else?" field should appear - type Seattle
        where_else = page.locator("input[aria-label='Where else?']")
        print(f"Where else count: {await where_else.count()}", flush=True)
        if await where_else.count() > 0:
            await where_else.first.type("Seattle", delay=60)
            await asyncio.sleep(2)
        else:
            # Try typing in the origin field
            await origin.first.type("Seattle", delay=60)
            await asyncio.sleep(2)

        # Print suggestion options
        opts = page.locator("[role='option']")
        print(f"Options: {await opts.count()}", flush=True)
        for i in range(min(await opts.count(), 15)):
            txt = await opts.nth(i).text_content()
            print(f"  {i}: {(txt or '')[:80]}", flush=True)

        # Click Seattle/SEA
        sea = opts.filter(has_text=re.compile(r"SEA", re.IGNORECASE)).first
        if await sea.count() > 0:
            await sea.click()
            await asyncio.sleep(1)
            print("Selected SEA", flush=True)
        else:
            # Try other text matches
            sea = opts.filter(has_text=re.compile(r"Seattle", re.IGNORECASE)).first
            if await sea.count() > 0:
                await sea.click()
                print("Selected Seattle (text)", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "expl_origin.png"))

        # Step 3: Destination - New York
        print("=== Step 3: Dest ===", flush=True)
        dest = page.locator("input[placeholder='Where to?']")
        await dest.first.click()
        await asyncio.sleep(1)

        where_else = page.locator("input[aria-label='Where else?']")
        if await where_else.count() > 0:
            await where_else.first.type("New York", delay=60)
        else:
            await dest.first.type("New York", delay=60)
        await asyncio.sleep(2)

        opts = page.locator("[role='option']")
        for i in range(min(await opts.count(), 15)):
            txt = await opts.nth(i).text_content()
            print(f"  {i}: {(txt or '')[:80]}", flush=True)

        nyc = opts.filter(has_text=re.compile(r"New York|JFK", re.IGNORECASE)).first
        if await nyc.count() > 0:
            await nyc.click()
            await asyncio.sleep(1)
            print("Selected NYC", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "expl_dest.png"))

        # Step 4: Departure
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

        await page.screenshot(path=str(SCREENSHOTS / "expl_date.png"))

        # Step 5: Search
        print("=== Step 5: Search ===", flush=True)
        btn = page.locator("button").filter(has_text="Explore destinations")
        if await btn.count() > 0:
            await btn.first.click()
        else:
            page.locator("button").filter(has_text="Explore").first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)
        await page.screenshot(path=str(SCREENSHOTS / "expl_results.png"))
        print(f"URL: {page.url[:300]}", flush=True)
        print(f"Title: {await page.title()}", flush=True)

        snapshot = await page.locator("body").aria_snapshot()
        print("\n=== Results ===", flush=True)
        print(snapshot[:15000], flush=True)

        await browser.close()

asyncio.run(main())
