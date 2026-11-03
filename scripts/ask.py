"""Ask your deployed GmailAgent from PowerShell.

Run: python ask.py "Summarize my latest emails"
Requires: pip install boto3 and configured AWS credentials.
"""
import json
import sys
import uuid

import boto3
from botocore.config import Config

REGION = "ca-central-1"
PROJECT_NAME = "GmailAgent"


def runtime_arn():
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)
    pager = control.get_paginator("list_agent_runtimes")
    for page in pager.paginate():
        for runtime in page.get("agentRuntimes", []):
            if PROJECT_NAME in runtime.get("agentRuntimeName", ""):
                return runtime["agentRuntimeArn"]
    raise SystemExit(f"No deployed {PROJECT_NAME} runtime found in {REGION}.")


def main():
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        prompt = input("Ask GmailAgent: ").strip()
    if not prompt:
        return

    client = boto3.client("bedrock-agentcore", region_name=REGION,
                          config=Config(read_timeout=300))
    result = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn(),
        qualifier="DEFAULT",
        runtimeSessionId="gmail-demo-" + uuid.uuid4().hex,
        contentType="application/json",
        payload=json.dumps({"prompt": prompt, "actorId": "demo"}).encode(),
    )

    collected = []
    body = result["response"]
    for raw in body.iter_lines():
        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        if not line.strip():
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        elif line.startswith(("event:", ":")):
            continue
        try:
            data = json.loads(line)
        except ValueError:
            collected.append(line)
            continue
        if isinstance(data, dict):
            if "error" in data:
                print("Error:", data["error"])
                return
            ev = data.get("event", data)
            delta = ev.get("contentBlockDelta", {}).get("delta", {}) if isinstance(ev, dict) else {}
            chunk = delta.get("text", "")
            if chunk:
                print(chunk, end="", flush=True)
                collected = ["printed"]
                continue
        if not collected:
            collected.append(line)
    print()
    if collected and collected != ["printed"]:
        print("\n".join(collected))


if __name__ == "__main__":
    main()
