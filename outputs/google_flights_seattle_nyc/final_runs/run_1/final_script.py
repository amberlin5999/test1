import asyncio, os, re
from pathlib import Path
from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

def log_msg(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    print(line, end="", flush=True)

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        # CP1: Navigate to Google Flights
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_homepage.png"))
        log_msg(1, "opened Google Flights homepage")

        # CP2: Set origin to Seattle
        origin = page.locator("input[aria-label='Where from?']")
        await origin.first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("Seattle", delay=60)
        await asyncio.sleep(2)
        await page.locator("[role='option']").nth(7).click()
        await asyncio.sleep(1)
        origin_val = await origin.first.input_value()
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_origin_seattle.png"))
        log_msg(2, f"set origin to Seattle (value='{origin_val}')")

        # CP3: Set destination to New York
        dest = page.locator("input[aria-label='Where to? ']")
        await dest.first.click()
        await asyncio.sleep(1.5)
        await page.keyboard.type("New York", delay=60)
        await asyncio.sleep(2)
        await page.locator("[role='option']").filter(has_text=re.compile(r"^New York, USA", re.IGNORECASE)).first.click()
        await asyncio.sleep(1)
        dest_val = await dest.first.input_value()
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_3_dest_nyc.png"))
        log_msg(3, f"set destination to New York (value='{dest_val}')")

        # CP4: Set departure date to August 15, 2026
        dep = page.locator("input[aria-label='Departure']").first
        await dep.click()
        await asyncio.sleep(0.5)
        await dep.fill("")
        await dep.type("Aug 15, 2026", delay=30)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)
        dep_val = await dep.input_value()
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_4_date_aug15.png"))
        log_msg(4, f"set departure date to Aug 15, 2026 (value='{dep_val}')")

        # CP5: Set ticket type to One way
        await page.get_by_role("combobox").filter(has_text=re.compile(r"Round trip|One way", re.IGNORECASE)).first.click()
        await asyncio.sleep(1)
        await page.get_by_role("option", name="One way").first.click()
        await asyncio.sleep(2)
        # Close any remaining dropdown
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_5_one_way.png"))
        log_msg(5, "set ticket type to One way")

        # CP6: Execute search via Enter (focus should be on the form after Escape)
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_6a_after_enter.png"))
        print(f"  After Enter URL: {page.url[:200]}", flush=True)

        # Handle price calendar dialog if present
        done_btn = page.get_by_role("button", name="Done")
        if await done_btn.count() > 0:
            await done_btn.first.click()
            await asyncio.sleep(2)
            log_msg(6, "dismissed price calendar dialog")

        # Check for and click "Search" or "Search for flights" button
        search_btn = page.get_by_role("button", name=re.compile(r"Search", re.IGNORECASE))
        if await search_btn.count() > 0:
            await search_btn.first.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(8)
            log_msg(6, "clicked Search button")

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_6_search_results.png"))
        print(f"  After search URL: {page.url[:200]}", flush=True)
        print(f"  Title: {await page.title()}", flush=True)

        # Get page snapshot
        await asyncio.sleep(3)
        snapshot = await page.locator("body").aria_snapshot()
        lines = snapshot.split('\n')
        print(f"  Snapshot length: {len(snapshot)} chars", flush=True)

        # Extract cheapest price
        cheapest_price = None
        cheapest_info = ""
        for line in lines:
            m = re.search(r'From (\d+) New Taiwan dollars', line, re.IGNORECASE)
            if m:
                price = int(m.group(1))
                if cheapest_price is None or price < cheapest_price:
                    cheapest_price = price
                    cheapest_info = line[:300]

        if cheapest_price is None:
            for line in lines:
                m = re.search(r'(\d{3,5}) New Taiwan dollars', line)
                if m:
                    price = int(m.group(1))
                    if cheapest_price is None or price < cheapest_price:
                        cheapest_price = price

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_7_cheapest_price.png"))

        result = f"Cheapest flight on Aug 15, 2026 from Seattle to New York: NT${cheapest_price:,}" if cheapest_price else "Cheapest flight on Aug 15, 2026 from Seattle to New York: Could not determine price (check screenshots)"
        log_msg(7, result)
        print(f"\n  {result}", flush=True)
        if cheapest_info:
            print(f"  Detail: {cheapest_info[:200]}", flush=True)

        with LOG.open("a") as f:
            f.write(f"\nFINAL_RESPONSE: {result}\n")

        await browser.close()

asyncio.run(main())
