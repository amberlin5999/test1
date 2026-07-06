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

        # Method: fill origin input directly using JS (native value setter)
        # This is the most reliable way for Google's framework
        print("=== Fill origin via JS ===", flush=True)
        result = await page.evaluate("""
        () => {
            const inp = document.querySelector('input[aria-label="Where from?"]');
            if (!inp) return 'NO_INPUT';
            
            // Focus
            inp.focus();
            inp.select();
            
            // Use the native React-compatible value setter
            // Google uses its own framework, but we can dispatch native events
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'value'
            ).set.call(inp, 'Seattle');
            
            // Dispatch input event (most frameworks listen for this)
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            inp.dispatchEvent(new Event('change', { bubbles: true }));
            
            return inp.value;
        }
        """)
        print(f"JS fill result: {result}", flush=True)
        await asyncio.sleep(2)

        # Check current state
        state = await page.evaluate("""() => {
            const els = document.querySelectorAll('input[aria-label]');
            return Array.from(els).map(e => ({
                label: e.getAttribute('aria-label'),
                val: e.value,
                visible: e.offsetParent !== null
            }));
        }""")
        print("=== Inputs after JS fill ===", flush=True)
        for s in state:
            print(f"  label='{s['label']}' val='{s['val']}' visible={s['visible']}", flush=True)

        await page.screenshot(path=str(SCREENSHOTS / "expl_js_fill.png"))

        # If origin overlay is open, try pressing Enter to confirm
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        # Check origin value
        origin_val = await page.evaluate("""() => 
            document.querySelector('input[aria-label="Where from?"]')?.value
        """)
        print(f"Origin after Escape: '{origin_val}'", flush=True)

        # Now try to fill destination via JS
        print("\n=== Fill dest via JS ===", flush=True)
        await page.evaluate("""
        () => {
            const inp = document.querySelector('input[aria-label="Where to? "]');
            if (!inp) return 'NO_INPUT';
            inp.focus();
            inp.select();
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'value'
            ).set.call(inp, 'New York');
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            inp.dispatchEvent(new Event('change', { bubbles: true }));
            return inp.value;
        }
        """)
        await asyncio.sleep(1)

        # Fill departure via JS
        print("=== Fill date via JS ===", flush=True)
        await page.evaluate("""
        () => {
            const inp = document.querySelector('input[aria-label="Departure"]');
            if (!inp) return 'NO_INPUT';
            inp.focus();
            inp.select();
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype, 'value'
            ).set.call(inp, 'Aug 15, 2026');
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            inp.dispatchEvent(new Event('change', { bubbles: true }));
            return inp.value;
        }
        """)
        await asyncio.sleep(1)

        state = await page.evaluate("""() => {
            const els = document.querySelectorAll('input[aria-label]');
            return Array.from(els).map(e => ({
                label: e.getAttribute('aria-label'),
                val: e.value,
                visible: e.offsetParent !== null
            }));
        }""")
        print("=== Inputs after all JS fills ===", flush=True)
        for s in state:
            print(f"  label='{s['label']}' val='{s['val']}' visible={s['visible']}", flush=True)

        # Try exploring
        btn = page.locator("button").filter(has_text="Explore destinations")
        if await btn.count() > 0:
            await btn.first.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)
            print(f"\nSearch URL: {page.url[:400]}", flush=True)
            print(f"Title: {await page.title()}", flush=True)
            await page.screenshot(path=str(SCREENSHOTS / "expl_js_search.png"))

            # Check form state after search
            snapshot = await page.locator("[role='search']").aria_snapshot()
            print(f"Search form:\n{snapshot[:3000]}", flush=True)

        await browser.close()

asyncio.run(main())
