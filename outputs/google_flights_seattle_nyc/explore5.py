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

        # Try navigating with tfs parameter in the URL for flight search
        # Using Google Flights search tfs with SEA->NYC on 2026-08-15
        # tfs=CBwQAxoo... format. Let's try a known pattern.
        
        # Navigate to flights first
        await page.goto("https://www.google.com/travel/flights", wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Try clicking the "Where from?" field, see the overlay
        origin_input = page.locator("input[aria-label='Where from?']")
        await origin_input.first.click()
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(SCREENSHOTS / "expl_click_origin.png"))

        # Get current overlay state
        state = await page.evaluate("""
        () => {
            // Check all the aria-labels in the page
            const inputs = document.querySelectorAll('input[aria-label]');
            return Array.from(inputs).map(el => ({
                label: el.getAttribute('aria-label'),
                value: el.value,
                placeholder: el.getAttribute('placeholder'),
                role: el.getAttribute('role'),
                visible: el.offsetParent !== null,
                autofocus: el.hasAttribute('autofocus')
            }));
        }
        """)
        print("=== All inputs ===", flush=True)
        for s in state:
            print(f"  visible={s['visible']} autofocus={s['autofocus']} label='{s['label']}' val='{s['value']}' placeholder='{s['placeholder']}' role='{s['role']}'", flush=True)

        await browser.close()

asyncio.run(main())
