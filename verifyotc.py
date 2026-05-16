#!/usr/bin/env python3
"""
AMD AI Developer Program - Step 3: Confirm opt-in emails
Finds and clicks the "Confirm Opt-In Request" links from AMD marketing emails.

Usage: python3 verifyotc.py
       python3 verifyotc.py --email "user1@domain.com,user2@domain.com"
       python3 verifyotc.py --all  (confirm ALL pending opt-ins)
"""
import sys
import json
import re
import imaplib
import email
import requests
import argparse

sys.stdout.reconfigure(line_buffering=True)

IMAP_EMAIL = os.environ.get("IMAP_EMAIL", "")
IMAP_PASS = os.environ.get("IMAP_PASS", "")
DOMAIN = os.environ.get("AMD_DOMAIN", "yourdomain.com")


def fetch_and_confirm(filter_emails=None, confirm_all=False):
    """Find opt-in confirmation emails and click the confirm links."""
    print("=== AMD Opt-In Confirmation ===\n")

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(IMAP_EMAIL, IMAP_PASS)
    mail.select('INBOX')

    # Search for opt-in confirmation emails
    status, messages = mail.search(None, 'FROM', '"reply@engage.amd.com"', 'SUBJECT', '"Confirm"')
    msg_ids = messages[0].split()
    print(f"Found {len(msg_ids)} confirmation emails\n")

    if not msg_ids:
        print("No opt-in emails found. They may arrive later (usually 5-15 min after activation).")
        mail.logout()
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    confirmed = 0
    skipped = 0
    failed = 0

    for msg_id in msg_ids:
        status, data = mail.fetch(msg_id, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        to_addr = msg['To'] or ''

        # Filter by email if specified
        if filter_emails and to_addr not in filter_emails:
            continue
        if not confirm_all and not filter_emails and DOMAIN not in to_addr:
            continue

        # Get HTML body
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        # Find confirm link (visit.amd.com/dc/...)
        dc_links = re.findall(r'https://visit\.amd\.com/dc/[^\s"<>\']+', body)

        if not dc_links:
            print(f"  ⚠️  {to_addr}: no confirm link found")
            skipped += 1
            continue

        # Click confirm link
        try:
            resp = requests.get(dc_links[0], headers=headers, timeout=15, allow_redirects=True)
            if resp.status_code in [200, 302]:
                print(f"  ✅ {to_addr}: confirmed")
                confirmed += 1
            else:
                print(f"  ❌ {to_addr}: HTTP {resp.status_code}")
                failed += 1
        except Exception as e:
            print(f"  ❌ {to_addr}: {str(e)[:60]}")
            failed += 1

    mail.logout()

    print(f"\n=== Results ===")
    print(f"  Confirmed: {confirmed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Failed:    {failed}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', type=str, help='Comma-separated emails to confirm')
    parser.add_argument('--all', action='store_true', help='Confirm all pending opt-ins for domain')
    args = parser.parse_args()

    filter_emails = None
    if args.email:
        filter_emails = [e.strip() for e in args.email.split(',')]

    fetch_and_confirm(filter_emails=filter_emails, confirm_all=args.all)


if __name__ == "__main__":
    main()
