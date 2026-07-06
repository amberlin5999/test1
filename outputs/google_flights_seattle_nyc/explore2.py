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
        await page.get_by_role("option").filter(has_text="One way").click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Step 2: Origin - Seattle
        print("=== Step 2: Origin ===", flush=True)
        origin = page.get_by_role("combobox", name="Where from?")
        await origin.first.click()
        await asyncio.sleep(0.5)
        await origin.first.press("Control+a")
        await asyncio.sleep(0.3)
        await origin.first.type("Seattle", delay=60)
        await asyncio.sleep(2)

        for i in range(min(await page.locator("[role='option']").count(), 10)):
            txt = await page.locator("[role='option']").nth(i).text_content()
            print(f"  {i}: {txt[:80] if txt else '-'}", flush=True)

        sea = page.locator("[role='option']").filter(has_text=re.compile(r"SEA", re.IGNORECASE)).first
        if await sea.count() > 0:
            await sea.click()
            await asyncio.sleep(1)
            print("Selected SEA", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "explore_origin.png"))

        # Step 3: Destination
        print("=== Step 3: Dest ===", flush=True)
        dest = page.get_by_role("combobox", name="Where to?")
        await dest.first.click()
        await asyncio.sleep(0.5)
        await dest.first.type("New York", delay=60)
        await asyncio.sleep(2)

        for i in range(min(await page.locator("[role='option']").count(), 10)):
            txt = await page.locator("[role='option']").nth(i).text_content()
            print(f"  {i}: {txt[:80] if txt else '-'}", flush=True)

        nyc = page.locator("[role='option']").filter(has_text=re.compile(r"New York|JFK", re.IGNORECASE)).first
        if await nyc.count() > 0:
            await nyc.click()
            await asyncio.sleep(1)
            print("Selected NYC", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "explore_dest.png"))

        # Step 4: Date
        print("=== Step 4: Date ===", flush=True)
        dep = page.get_by_role("textbox", name="Departure")
        if await dep.count() > 0:
            await dep.first.click()
            await asyncio.sleep(0.5)
            await dep.first.press("Control+a")
            await asyncio.sleep(0.3)
            await dep.first.type("Aug 15, 2026", delay=30)
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)
            print(f"Date value: '{await dep.input_value()}'", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "explore_date.png"))

        # Step 5: Search
        print("=== Step 5: Search ===", flush=True)
        btn = page.get_by_role("button", name="Explore destinations")
        if await btn.count() > 0:
            await btn.click()
        else:
            page.get_by_role("button").filter(has_text="Explore").first.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)
        await page.screenshot(path=str(SCREENSHOTS / "explore_results.png"))
        print(f"URL: {page.url[:300]}", flush=True)
        print(f"Title: {await page.title()}", flush=True)

        snapshot = await page.locator("body").aria_snapshot()
        print("\n=== Results ===", flush=True)
        print(snapshot[:15000], flush=True)

        await browser.close()

asyncio.run(main())
