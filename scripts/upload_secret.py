"""Upload gmail-token.json to AWS Secrets Manager (creates it, or updates it if it exists).

Usage:  python upload_secret.py ca-central-1
Prints the secret ARN - you need it for the permission step.
"""
import sys
from pathlib import Path

import boto3

REGION = sys.argv[1] if len(sys.argv) > 1 else "ca-central-1"
NAME = "gmail-agent-demo"  # must match SECRET_NAME in main.py

token = Path("gmail-token.json")
if not token.is_file():
    raise SystemExit("gmail-token.json not found. Run bootstrap_gmail.py first.")

sm = boto3.client("secretsmanager", region_name=REGION)
body = token.read_text(encoding="utf-8")
try:
    sm.create_secret(Name=NAME, SecretString=body)
    print(f"Created secret '{NAME}' in {REGION}")
except sm.exceptions.ResourceExistsException:
    sm.put_secret_value(SecretId=NAME, SecretString=body)
    print(f"Updated secret '{NAME}' in {REGION}")
print("Secret ARN:", sm.describe_secret(SecretId=NAME)["ARN"])
