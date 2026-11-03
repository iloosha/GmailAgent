# Gmail Reader Agent on AWS AgentCore

An AI agent that reads your Gmail (read-only), tells you what is important and summarizes recent mail.
Built with the AgentCore CLI + Strands, deployed to **AgentCore Runtime** in `ca-central-1`.

```
python scripts/ask.py "..."  ->  AgentCore Runtime (app/agent/main.py)
                                   tools: search_emails, read_email
                                   Gmail API (read-only)  <-  OAuth token in AWS Secrets Manager
```

## Layout

| Path | What it is |
|---|---|
| `app/agent/main.py` | The agent: system prompt, the two Gmail tools, model choice |
| `agentcore/agentcore.json` | AgentCore project config (runtime + memory) |
| `scripts/bootstrap_gmail.py` | One-time Google sign-in on your laptop, writes `gmail-token.json` |
| `scripts/upload_secret.py` | Saves that token to AWS Secrets Manager (`gmail-agent-demo`) |
| `scripts/ask.py` | Ask the deployed agent a question from the terminal |
| `scripts/secret-policy.example.json` | IAM policy that lets the agent read the secret |

## Run your own copy (about 30 minutes, your own AWS account and Gmail)

Needs: AWS CLI configured for `ca-central-1`, Node.js 20+, Python 3.10+,
`npm install -g @aws/agentcore`, [uv](https://docs.astral.sh/uv/), `pip install google-auth-oauthlib boto3`.

1. **Google Cloud:** new project > enable *Gmail API* > Google Auth Platform: audience *External*, add yourself as a
   *test user*, add scope `https://www.googleapis.com/auth/gmail.readonly` > create an OAuth client of type
   **Desktop app** > download the JSON as `credentials.json` into the repo root (it is gitignored).
2. **Sign in once and store the token** (from the repo root):
   ```
   python scripts/bootstrap_gmail.py
   python scripts/upload_secret.py ca-central-1      # prints the Secret ARN
   ```
3. **Deploy** (PowerShell: `$env:AWS_REGION="ca-central-1"`; bash: `export AWS_REGION=ca-central-1`):
   ```
   agentcore deploy
   ```
4. **Let the agent read the secret.** Copy `scripts/secret-policy.example.json` to `scripts/secret-policy.json`, paste your
   Secret ARN, then attach it to the runtime's execution role (the one with `Runtime` in its name):
   ```
   aws iam list-roles --query "Roles[?contains(RoleName,'GmailAgent')].RoleName" --output text
   aws iam put-role-policy --role-name <RUNTIME_ROLE> --policy-name gmail-secret --policy-document file://scripts/secret-policy.json
   ```
5. **Ask it:** `python scripts/ask.py "Summarize my 10 most recent emails. What is urgent?"`

## Model

The model is set in `app/agent/main.py` (`_get_agent`): Amazon Nova 2 Lite (`us.amazon.nova-2-lite-v1:0`) in `ca-central-1`.
`app/agent/model/load.py` still points at Claude but is not used. Swap the model there if Claude is enabled on your account.

## Cost and cleanup

Cost comes mainly from **model tokens** on every question. AgentCore Runtime bills only for active session time.
`agentcore.json` also creates an **AgentCore Memory** resource with four strategies, so session content (including email
summaries) is stored in your account for 30 days and can add small charges. Secrets Manager is about $0.40 per secret
per month. When you are done:

```
aws cloudformation delete-stack --stack-name AgentCore-GmailAgent-default --region ca-central-1
aws secretsmanager delete-secret --secret-id gmail-agent-demo --force-delete-without-recovery --region ca-central-1
```
Then revoke the app at https://myaccount.google.com/permissions and delete the OAuth client in Google Cloud.

## Security

- **Never commit** `credentials.json` or `gmail-token.json` (both are in `.gitignore`).
- Read-only Gmail scope. Google test-mode tokens expire after about 7 days: re-run step 2.
- Single-user demo: anyone allowed to invoke the runtime can read the owner's mail. Email text is treated as untrusted data.
