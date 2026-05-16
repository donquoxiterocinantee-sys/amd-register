#!/usr/bin/env python3
"""
AMD AI Developer Program - Step 2: Activate accounts (set password)
Reads activation tokens from email, then submits token + password via browser.

Usage: DISPLAY=:99 python3 activate.py --input amd_registered_20260516.json
       DISPLAY=:99 python3 activate.py --email "user1@domain.com,user2@domain.com"
"""
import asyncio
import cloakbrowser
import os
import sys
import json
import re
import imaplib
import email
import html as htmlmod
import time

sys.stdout.reconfigure(line_buffering=True)
os.environ["DISPLAY"] = ":99"

IMAP_EMAIL = os.environ.get("IMAP_EMAIL", "")
IMAP_PASS = os.environ.get("IMAP_PASS", "")
PASSWORD = "Anggy123!!"
PROXY = {
    "server": os.environ.get("PROXY_SERVER", "http://proxy:port"),
    "username": os.environ.get("PROXY_USER", ""),
    "password": os.environ.get("PROXY_PASS", "")
}
ACTIVATE_URL = "https://www.amd.com/en/registration/activate-account.html"


def fetch_tokens(emails):
    """Fetch activation tokens from IMAP for given email addresses."""
    print(f"=== Fetching tokens for {len(emails)} accounts ===\n")
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(IMAP_EMAIL, IMAP_PASS)
    mail.select('INBOX')

    tokens = {}
    missing = []

    for addr in emails:
        status, messages = mail.search(None, 'TO', f'"{addr}"', 'SUBJECT', '"activate"')
        msg_ids = messages[0].split()

        if not msg_ids:
            print(f"  ⏳ {addr}: no email yet")
            missing.append(addr)
            continue

        status, data = mail.fetch(msg_ids[-1], '(RFC822)')
        msg = email.message_from_bytes(data[0][1])

        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == 'text/html':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                elif ct == 'text/plain' and not body:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        clean = re.sub(r'<[^>]+>', '|||', body)
        clean = htmlmod.unescape(clean)
        m = re.search(r'Token is:\s*\|*\s*([A-Za-z0-9_\-]{5,30})', clean)
        if m:
            tokens[addr] = m.group(1)
            print(f"  ✅ {addr}: {m.group(1)}")
        else:
            print(f"  ❌ {addr}: token not found in email body")
            missing.append(addr)

    mail.logout()

    if missing:
        print(f"\n  Missing: {len(missing)} — emails may still be arriving, retry later")

    return tokens


async def activate_one(email_addr, token, idx, total):
    """Activate a single account via browser."""
    print(f"\n[{idx+1}/{total}] {email_addr}")

    browser = await cloakbrowser.launch_async(headless=True, args=['--no-sandbox', '--disable-gpu'], proxy=PROXY)
    page = await browser.new_page()

    try:
        await page.goto(ACTIVATE_URL, wait_until='load', timeout=60000)
        await page.wait_for_selector('#form-text-30246375', state='visible', timeout=30000)

        # Dismiss cookie
        await page.evaluate('() => { const b = document.getElementById("onetrust-accept-btn-handler"); if(b) b.click(); }')
        await page.wait_for_timeout(2000)

        # Fill activation form
        await page.fill('#form-text-30246375', token)
        await page.fill('#form-text-766004985', PASSWORD)
        await page.fill('#form-text-766004985_confirm', PASSWORD)
        await page.wait_for_timeout(1000)
        await page.evaluate('() => { const btns = document.querySelectorAll(".cmp-form-button"); for (const btn of btns) { if (btn.textContent.trim()) { btn.click(); break; } } }')

        # Wait for Akamai challenge + resubmit
        for i in range(8):
            await page.wait_for_timeout(5000)
            text = ''
            try:
                text = await page.inner_text('body')
            except:
                pass
            url = page.url

            if 'developer.amd.com' in url or 'success' in text.lower() or 'activated' in text.lower() or 'congratulations' in text.lower():
                print(f"  ✅ Activated")
                return True

            if len(text) > 500 and 'Access Token' in text:
                # Form reappeared after challenge — resubmit
                try:
                    await page.wait_for_selector('#form-text-30246375', state='visible', timeout=5000)
                except:
                    pass
                await page.fill('#form-text-30246375', token)
                await page.fill('#form-text-766004985', PASSWORD)
                await page.fill('#form-text-766004985_confirm', PASSWORD)
                await page.wait_for_timeout(1000)
                await page.evaluate('() => { const btns = document.querySelectorAll(".cmp-form-button"); for (const btn of btns) { if (btn.textContent.trim()) { btn.click(); break; } } }')
                await page.wait_for_timeout(15000)

                url2 = page.url
                text2 = ''
                try:
                    text2 = await page.inner_text('body')
                except:
                    pass

                if 'developer.amd.com' in url2 or 'success' in text2.lower() or 'activated' in text2.lower() or 'congratulations' in text2.lower():
                    print(f"  ✅ Activated (resubmit)")
                    return True
                elif 'invalid' in text2.lower() or 'expired' in text2.lower():
                    print(f"  ❌ Token invalid/expired")
                    return False
                else:
                    print(f"  ❌ Failed")
                    return False

        print(f"  ❌ Timeout")
        return False

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:80]}")
        return False
    finally:
        try:
            await browser.close()
        except:
            pass


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, help='JSON file from register.py')
    parser.add_argument('--email', type=str, help='Comma-separated email addresses')
    parser.add_argument('--wait', type=int, default=0, help='Seconds to wait before fetching tokens')
    args = parser.parse_args()

    # Get email list
    emails = []
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
        emails = [r['email'] for r in data if r.get('status') == 'registered']
    elif args.email:
        emails = [e.strip() for e in args.email.split(',')]
    else:
        print("Error: provide --input or --email")
        sys.exit(1)

    if not emails:
        print("No emails to activate")
        sys.exit(0)

    # Optional wait for emails to arrive
    if args.wait > 0:
        print(f"Waiting {args.wait}s for activation emails to arrive...")
        time.sleep(args.wait)

    # Fetch tokens
    tokens = fetch_tokens(emails)

    if not tokens:
        print("\nNo tokens found. Emails may not have arrived yet.")
        print("Retry: python3 activate.py --email \"addr1,addr2\"")
        sys.exit(1)

    # Activate
    print(f"\n=== Activating {len(tokens)} accounts | pw: {PASSWORD} ===")
    success = []
    failed = []

    for idx, (addr, token) in enumerate(tokens.items()):
        result = await activate_one(addr, token, idx, len(tokens))
        if result:
            success.append(addr)
        else:
            failed.append(addr)
        await asyncio.sleep(2)

    print(f"\n=== Results: {len(success)}/{len(tokens)} activated ===")
    for e in success:
        print(f"  ✅ {e}")
    for e in failed:
        print(f"  ❌ {e}")


if __name__ == "__main__":
    asyncio.run(main())
