
import asyncio
import random
import json
from playwright.async_api import async_playwright

async def main(account):
    # Read account info from JSON
    name = account["name"]
    email = account["email"]
    password = account["password"]
    country = account.get("country", "United States")
    gender = account.get("gender", "male")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.bimileap.com/signup")

        print("[INFO] Filling name, email, password...")
        await page.fill('input[placeholder="Name*"]', name)
        await page.fill('input[placeholder="Email*"]', email)
        await page.fill('input[placeholder="Password*"]', password)

        print("[INFO] Opening date picker...")
        await page.click('input[placeholder="Birthdate*"]')
        await asyncio.sleep(1.0)

        # Pick a valid day
        day_cells = await page.query_selector_all('span.cell.day')
        valid_days = []
        for d in day_cells:
            text = await d.inner_text()
            if text.strip().isdigit():
                valid_days.append((d, int(text.strip())))
        if not valid_days:
            print("[ERROR] No valid days found.")
            await asyncio.sleep(10)
            await browser.close()
            return
        selected, day_num = random.choice(valid_days)
        print(f"[INFO] Clicking day: {day_num}")
        await selected.click()

        # Select country from dropdown
        print(f"[INFO] Selecting country: {country}")
        try:
            result = await page.select_option('select.country-placeholder', value=country)
            print(f"[DEBUG] select_option result: {result}")
            if not result or result[0] is None:
                raise Exception("select_option returned no result, trying fallback...")
        except Exception as e:
            print(f"[WARN] select_option failed: {e}")
            await page.click('select.country-placeholder')
            await asyncio.sleep(0.3)
            option = await page.query_selector(f'option[value="{country}"]')
            if option:
                await option.click()
                print(f"[SUCCESS] Clicked country option: {country}")
            else:
                print(f"[ERROR] Could not find country option: {country}")

        # Select gender radio button
        print(f"[INFO] Selecting gender: {gender}")
        if gender.lower() in ["male", "female"]:
            await page.check(f'input[type="radio"]#{gender.lower()}')
            print(f"[SUCCESS] Selected gender: {gender}")
        else:
            print(f"[WARN] Gender value '{gender}' not recognized; skipping.")

        # Agree to terms of service checkbox
        print("[INFO] Checking 'agree to terms' checkbox...")
        await page.check('input[type="checkbox"]#agree')
        print("[SUCCESS] Checked the terms of service box.")

        # Submit the form
        print("[INFO] Clicking Submit button...")
        await page.click('button[type="submit"].pure-button.bigmi-wide-button.bigmi-red-2-button')
        print("[SUCCESS] Submit button clicked.")

        await asyncio.sleep(10)
        await browser.close()

