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

        # 1) One way
        await page.get_by_role("combobox").filter(has_text="Round trip").first.click()
        await asyncio.sleep(1)
        await page.get_by_role("option").filter(has_text="One way").click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Inspect ALL combobox elements
        html = await page.evaluate("""
        () => {
            const combos = document.querySelectorAll('[role="combobox"]');
            return JSON.stringify(Array.from(combos).map(el => ({
                tag: el.tagName,
                type: el.getAttribute('type'),
                ariaLabel: el.getAttribute('aria-label'),
                value: el.value !== undefined ? el.value : el.textContent,
                placeholder: el.getAttribute('placeholder'),
                outerHTML: el.outerHTML.substring(0, 500)
            })));
        }
        """)
        print("=== All comboboxes ===", flush=True)
        print(html[:8000], flush=True)

        # Check departure field
        html2 = await page.evaluate("""
        () => {
            // Look for date inputs
            const allInputs = document.querySelectorAll('input[type="text"], input:not([type])');
            const results = [];
            allInputs.forEach(el => {
                const al = el.getAttribute('aria-label');
                const ph = el.getAttribute('placeholder');
                if (al && (al.toLowerCase().includes('depart') || al.toLowerCase().includes('date'))) {
                    results.push({ariaLabel: al, placeholder: ph, outerHTML: el.outerHTML.substring(0, 400)});
                }
                if (ph && (ph.toLowerCase().includes('depart') || ph.toLowerCase().includes('date'))) {
                    results.push({ariaLabel: al, placeholder: ph, outerHTML: el.outerHTML.substring(0, 400)});
                }
            });
            return JSON.stringify(results);
        }
        """)
        print("\n=== Date fields ===", flush=True)
        print(html2[:3000], flush=True)

        # Also try getting the whole form area
        html3 = await page.evaluate("""
        () => {
            const form = document.querySelector('[role="search"]');
            if (!form) return 'no search role';
            return form.outerHTML.substring(0, 5000);
        }
        """)
        print("\n=== Search form HTML ===", flush=True)
        print(html3[:5000], flush=True)

        await browser.close()

asyncio.run(main())
