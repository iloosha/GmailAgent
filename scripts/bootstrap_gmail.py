"""One-time local authorization: create read-only Gmail token JSON for AWS Secrets Manager.

1. In Google Cloud, create an OAuth client of type Desktop app.
2. Download its JSON to credentials.json (same directory).
3. Run: python -m pip install google-auth-oauthlib
4. Run: python bootstrap_gmail.py
5. Upload gmail-token.json to AWS Secrets Manager (do not commit either JSON).
"""
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
client_file = Path("credentials.json")
if not client_file.is_file():
    raise SystemExit("Missing credentials.json from your Google Cloud Desktop OAuth client")

flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes=SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
if not creds.refresh_token:
    raise SystemExit("Google returned no refresh token. Revoke test-app access and try again.")

output = Path("gmail-token.json")
output.write_text(creds.to_json(), encoding="utf-8")
if os.name != "nt":
    output.chmod(0o600)
print(f"Saved {output} locally. Upload it as SecretString to AWS Secrets Manager.")
print("Never commit or share credentials.json or gmail-token.json.")
