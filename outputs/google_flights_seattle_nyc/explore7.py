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

        # Step 2: Origin
        print("=== Step 2: Origin ===", flush=True)
        origin = page.locator("input[aria-label='Where from?']")
        await origin.first.click()
        await asyncio.sleep(1.5)

        # Type in the focused element
        await page.keyboard.type("Seattle", delay=60)
        await asyncio.sleep(2)

        # Print all options 
        opts = page.locator("[role='option']")
        for i in range(await opts.count()):
            txt = await opts.nth(i).text_content()
            print(f"  {i}: {(txt or '')[:80]}", flush=True)

        # Try clicking "Seattle" (index 7) specifically - the first geographic option
        if await opts.count() >= 8:
            await opts.nth(7).click()
            await asyncio.sleep(2)
            print("Clicked option 7 (Seattle)", flush=True)

        # Check full input state
        state = await page.evaluate("""() => {
            const els = document.querySelectorAll('input[aria-label]');
            return Array.from(els).map(e => ({
                label: e.getAttribute('aria-label'),
                val: e.value,
                visible: e.offsetParent !== null,
                placeholder: e.getAttribute('placeholder')
            }));
        }""")
        print("=== Inputs ===", flush=True)
        for s in state:
            print(f"  visible={s['visible']} label='{s['label']}' val='{s['val']}' placeholder='{s['placeholder']}'", flush=True)

        # Try to see the full form HTML
        html = await page.evaluate("""() => {
            const searchForm = document.querySelector('[role="search"]');
            if (!searchForm) return 'NO_FORM';
            return searchForm.querySelector('div[jsname]')?.querySelectorAll('div[class]')?.length || 'no children';
        }""")
        print(f"\nForm children: {html}", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "expl_origin_debug.png"))

        # Try selecting "Where from?" by clicking and pressing Enter
        origin2 = page.locator("input[aria-label='Where from?']")
        if await origin2.count() > 0 and await origin2.first.input_value() != "":
            print(f"Origin value: '{await origin2.first.input_value()}'", flush=True)
        else:
            print("Origin input not found or empty", flush=True)

        await browser.close()

asyncio.run(main())
