# AMD AI Developer Program - Auto Register

Automated registration, activation, and opt-in confirmation for the AMD AI Developer Program.

## How It Works

1. **register.py** — Creates accounts via browser automation (bypasses Akamai Bot Manager)
2. **activate.py** — Fetches activation tokens from email (IMAP), sets password via browser
3. **verifyotc.py** — Confirms opt-in marketing emails via HTTP GET

## Requirements

- Python 3.10+
- CloakBrowser (Playwright-based stealth browser)
- Residential proxy (for Akamai bypass)
- IMAP access to catch-all email

## Setup

```bash
pip install playwright requests
```

Create a `config.json` in the script directory:

```json
{
  "domain": "yourdomain.com",
  "imap_email": "your-catchall@gmail.com",
  "imap_pass": "your-app-password",
  "password": "YourPassword10!",
  "proxy": {
    "server": "http://proxy:port",
    "username": "user",
    "password": "pass"
  }
}
```

## Usage

### Step 1: Register

```bash
DISPLAY=:99 python3 register.py --count 10
```

Outputs `amd_registered_<timestamp>.json` with registered emails.

### Step 2: Activate

Wait 1-2 minutes for activation emails to arrive, then:

```bash
DISPLAY=:99 python3 activate.py --input amd_registered_20260516_185523.json
# or
DISPLAY=:99 python3 activate.py --email "user1@domain.com,user2@domain.com"
# with delay
DISPLAY=:99 python3 activate.py --wait 60 --input file.json
```

### Step 3: Confirm Opt-In

Wait 5-15 minutes after activation:

```bash
python3 verifyotc.py --all
# or specific emails
python3 verifyotc.py --email "user1@domain.com"
```

## Flow

```
register.py → (wait 1-2 min) → activate.py → (wait 5-15 min) → verifyotc.py
```

## Technical Notes

- AMD uses Akamai Bot Manager with crypto challenges — pure HTTP requests are blocked
- Flow: submit form → Akamai challenge (~30s) → form reappears → resubmit → success
- Activation tokens are 20 chars (alphanumeric + `-` and `_`)
- Password requires minimum 10 characters
- Opt-in confirmation is a simple HTTP GET to `visit.amd.com/dc/...` tracking link

## Disclaimer

For educational purposes only. Use responsibly.
