import getpass
import json
import os
import stat

# This must match OUTPUT_BASE in xbd3.py
OUTPUT_BASE = r'C:\Users\YourName\Pictures\X Bookmarks'
creds_file = os.path.join(OUTPUT_BASE, '_creds.json')

print("=== One-time credential setup ===")
print()
print("1. Press F12 in Chrome")
print("2. Click 'Application' tab")
print("3. Left panel: Cookies > https://x.com")
print("4. Find 'auth_token' row, copy its Value")
print("5. Inputs are hidden for safety")
print()
auth_token = getpass.getpass("Paste your auth_token here: ").strip()

ct0 = getpass.getpass("Paste your ct0 cookie value here (same place, find 'ct0' row): ").strip()

if not auth_token or not ct0:
    raise SystemExit("Both auth_token and ct0 are required.")

creds = {"auth_token": auth_token, "ct0": ct0}
os.makedirs(os.path.dirname(creds_file), exist_ok=True)
with open(creds_file, 'w') as f:
    json.dump(creds, f)

try:
    if os.name == 'nt':
        os.chmod(creds_file, stat.S_IREAD | stat.S_IWRITE)
    else:
        os.chmod(creds_file, 0o600)
except Exception:
    pass

print()
print(f"Saved to {creds_file}")
print("You only need to do this again if X logs you out.")
