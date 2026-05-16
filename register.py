#!/usr/bin/env python3
"""
AMD AI Developer Program - Step 1: Register accounts
Usage: DISPLAY=:99 python3 register.py --count 5
Output: amd_registered_<timestamp>.json
"""
import asyncio
import cloakbrowser
import os
import sys
import json
import random
from datetime import datetime

sys.stdout.reconfigure(line_buffering=True)
os.environ["DISPLAY"] = ":99"

DOMAIN = os.environ.get("AMD_DOMAIN", "yourdomain.com")
PROXY = {
    "server": os.environ.get("PROXY_SERVER", "http://proxy:port"),
    "username": os.environ.get("PROXY_USER", ""),
    "password": os.environ.get("PROXY_PASS", "")
}
REGISTER_URL = "https://www.amd.com/en/registration/ai-dev-program-sign-up-form.html"
CUSTTARG = "aHR0cHM6Ly9kZXZlbG9wZXIuYW1kLmNvbT9SZWxheVN0YXRlPQ=="

PEOPLE_POOL = [
    {"first": "James", "last": "Wilson", "company": "Stanford University", "country": "United States"},
    {"first": "Emma", "last": "Thompson", "company": "Imperial College London", "country": "United Kingdom"},
    {"first": "Hiroshi", "last": "Yamamoto", "company": "University of Tokyo", "country": "Japan"},
    {"first": "Priya", "last": "Sharma", "company": "IIT Bombay", "country": "India"},
    {"first": "Lars", "last": "Eriksson", "company": "KTH Royal Institute", "country": "Sweden"},
    {"first": "Chen", "last": "Wei", "company": "Peking University", "country": "China"},
    {"first": "Marco", "last": "Bianchi", "company": "Sapienza University", "country": "Italy"},
    {"first": "Sarah", "last": "O'Brien", "company": "Trinity College Dublin", "country": "Ireland"},
    {"first": "Ahmed", "last": "Mansour", "company": "AUC", "country": "Egypt"},
    {"first": "Julia", "last": "Schneider", "company": "TU Munich", "country": "Germany"},
    {"first": "Kenji", "last": "Nakamura", "company": "Kyoto University", "country": "Japan"},
    {"first": "Ana", "last": "Garcia", "company": "Universidad Complutense", "country": "Spain"},
    {"first": "Viktor", "last": "Petrov", "company": "Skoltech", "country": "Russian Federation"},
    {"first": "Lisa", "last": "van der Berg", "company": "TU Delft", "country": "Netherlands"},
    {"first": "Ravi", "last": "Kumar", "company": "IISc Bangalore", "country": "India"},
    {"first": "David", "last": "Park", "company": "Seoul National University", "country": "Korea, Republic of"},
    {"first": "Michael", "last": "Brown", "company": "MIT", "country": "United States"},
    {"first": "Yuki", "last": "Sato", "company": "Osaka University", "country": "Japan"},
    {"first": "Roberto", "last": "Ferreira", "company": "UNICAMP", "country": "Brazil"},
    {"first": "Nina", "last": "Johansson", "company": "Uppsala University", "country": "Sweden"},
    {"first": "Sophie", "last": "Dubois", "company": "Ecole Polytechnique", "country": "France"},
    {"first": "Tom", "last": "Mitchell", "company": "University of Toronto", "country": "Canada"},
    {"first": "Ingrid", "last": "Larsen", "company": "NTNU", "country": "Norway"},
    {"first": "Pablo", "last": "Rodriguez", "company": "Universidad de Buenos Aires", "country": "Argentina"},
    {"first": "Mika", "last": "Virtanen", "company": "Aalto University", "country": "Finland"},
    {"first": "Hassan", "last": "Ali", "company": "NUST", "country": "Pakistan"},
    {"first": "Rachel", "last": "Green", "company": "University of Melbourne", "country": "Australia"},
    {"first": "Oliver", "last": "Schmidt", "company": "ETH Zurich", "country": "Switzerland"},
    {"first": "Fatima", "last": "Benali", "company": "KAUST", "country": "Saudi Arabia"},
    {"first": "Daniel", "last": "Kim", "company": "KAIST", "country": "Korea, Republic of"},
]


async def register_one(person, idx, total):
    email_addr = f"{person['first'].lower()}.{person['last'].lower()}{random.randint(10,99)}@{DOMAIN}"
    print(f"\n[{idx+1}/{total}] {person['first']} {person['last']} | {email_addr} | {person['country']}")

    browser = await cloakbrowser.launch_async(headless=True, args=['--no-sandbox', '--disable-gpu'], proxy=PROXY)
    page = await browser.new_page()

    try:
        await page.goto(f"{REGISTER_URL}?custtarg={CUSTTARG}", wait_until='load', timeout=60000)
        await page.wait_for_selector('#form-text-1444782869', state='visible', timeout=30000)

        # Dismiss cookie banner
        await page.evaluate('() => { const b = document.getElementById("onetrust-accept-btn-handler"); if(b) b.click(); }')
        await page.wait_for_timeout(2000)

        # Fill form
        await page.fill('#form-text-1444782869', person['first'])
        await page.fill('#form-text-1891447162', person['last'])
        await page.fill('#form-text-1830320319', email_addr)
        await page.fill('#form-text-417351009', person['company'])
        await page.select_option('#country-dropdown-1299606956', label=person['country'])
        try:
            await page.select_option('#language-dropdown-765462299', label='English')
        except:
            pass
        await page.evaluate('() => { document.querySelectorAll("#new_form input[type=checkbox]").forEach(cb => { if(!cb.checked) cb.click(); }); }')
        await page.wait_for_timeout(1000)

        # Submit (triggers Akamai challenge)
        await page.evaluate('() => document.getElementById("form-button-1857186030").click()')

        # Wait for challenge + resubmit
        for i in range(8):
            await page.wait_for_timeout(5000)
            text = ''
            try:
                text = await page.inner_text('body')
            except:
                pass

            if 'activate' in page.url.lower():
                print(f"  ✅ Registered")
                return {"email": email_addr, "person": person, "status": "registered"}

            if len(text) > 500 and 'First Name' in text:
                # Resubmit after Akamai challenge solved
                await page.fill('#form-text-1444782869', person['first'])
                await page.fill('#form-text-1891447162', person['last'])
                await page.fill('#form-text-1830320319', email_addr)
                await page.fill('#form-text-417351009', person['company'])
                await page.select_option('#country-dropdown-1299606956', label=person['country'])
                try:
                    await page.select_option('#language-dropdown-765462299', label='English')
                except:
                    pass
                await page.evaluate('() => { document.querySelectorAll("#new_form input[type=checkbox]").forEach(cb => { if(!cb.checked) cb.click(); }); }')
                await page.wait_for_timeout(1000)
                await page.evaluate('() => document.getElementById("form-button-1857186030").click()')
                await page.wait_for_timeout(15000)

                if 'activate' in page.url.lower():
                    print(f"  ✅ Registered")
                    return {"email": email_addr, "person": person, "status": "registered"}
                break

        print(f"  ❌ Failed")
        return {"email": email_addr, "person": person, "status": "failed"}

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return {"email": email_addr, "person": person, "status": "error"}
    finally:
        try:
            await browser.close()
        except:
            pass


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=5)
    args = parser.parse_args()

    people = PEOPLE_POOL.copy()
    random.shuffle(people)
    people = people[:args.count]

    print(f"=== AMD Register — {len(people)} accounts ===")
    print(f"Domain: @{DOMAIN}\n")

    results = []
    for i, p in enumerate(people):
        result = await register_one(p, i, len(people))
        results.append(result)
        await asyncio.sleep(random.uniform(2, 5))

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"/root/BOT/amd_registered_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    registered = [r for r in results if r['status'] == 'registered']
    print(f"\n=== {len(registered)}/{len(results)} registered ===")
    for r in registered:
        print(f"  ✅ {r['email']}")
    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
