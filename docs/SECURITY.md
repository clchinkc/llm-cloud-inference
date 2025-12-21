# Security Guide

Complete guide to securing your LLM Cloud Inference deployment on Google Cloud Run.

## Overview

This guide covers implementing **IAM + Identity Tokens** security for production deployments. This approach:
- Uses Google Cloud's native identity and access management
- Requires no shared API keys
- Provides audit logging of all access
- Supports fine-grained access control

**Default**: All deployments use IAM + Identity Tokens. No shared secrets, no API keys to manage.

---

## Security Levels Reference

This section explains different security approaches for your understanding. The default IAM + Identity Tokens approach is recommended for all production use cases.

### Level 1: Development (Unauthenticated)

**Use case**: Local testing, development, internal team prototyping

**How it works**:
- Service is publicly accessible without authentication
- Anyone with the URL can make requests
- No IAM bindings needed
- Useful for quick testing and demos

**Security model**: Trust-on-first-use (suitable only for development)

**Risks**:
- No access control or audit trail
- Exposed to public internet
- Rate limiting depends on Cloud Run quotas
- Not suitable for any sensitive data or production use

**Trade-offs**: Maximum convenience, zero security

---

### Level 2: Identity-Based Access Control (Default - IAM + Identity Tokens)

**Use case**: Production deployments, team access, application-to-API communication

**How it works**:
1. Service requires valid Google Cloud identity (person or service account)
2. Identity tokens are cryptographically signed by Google
3. Cloud IAM checks token signature and user permissions
4. Access is automatically audited in Cloud Logging
5. Tokens automatically expire and refresh

**Security model**: Identity verification + role-based access control

**Who authenticates**:
- **Users**: Via `gcloud auth` or their Google account
- **Applications**: Via service account keys or Application Default Credentials
- **CI/CD**: Via Workload Identity or service account impersonation

**Key benefits**:
- No API keys to manage or rotate
- Automatic audit trail of all access
- Fine-grained per-user/app access control
- Tokens auto-expire (1 hour default)
- Google Cloud native (automatic in GCP ecosystem)
- Access control from individual users to organizations
- Temporary access revocation (instant)

**Trade-offs**: Requires Google Cloud authentication setup (minimal overhead for users already in GCP ecosystem)

---

### Level 3: Network Isolation (VPC Connector)

**Use case**: Highly sensitive applications, private network access only

**How it works**:
- Service runs inside a Virtual Private Cloud (VPC)
- Access only from other resources in the same network
- Requires VPN/bastion host for external access
- Combines network isolation + IAM

**Security model**: Network isolation + identity verification

**Additional cost**: ~$1-5/month for VPC connector

**Appropriate for**: Organizations with strict network policies, HIPAA/PCI compliance

---

### Level 4: Advanced Rate Limiting & DDoS Protection (Cloud Armor)

**Use case**: Public APIs, high-traffic services, DDoS protection required

**How it works**:
- Cloud Armor sits in front of Cloud Run
- Can rate limit by IP, geographic location, custom rules
- Blocks DDoS attacks at the network edge
- Logs all blocked requests

**Additional cost**: ~$10-50/month depending on rules

**Appropriate for**: Commercial APIs, public-facing services

---

## Which Level to Use?

| Level | Cost | Setup Time | Audit Trail | Access Control | Best For |
|-------|------|-----------|------------|---|---|
| **1: Dev** | $0 | 0 min | ❌ No | ❌ None | Testing only |
| **2: IAM (Default)** | $0 | 2 min | ✅ Yes | ✅ Per-user | Production |
| **3: VPC** | +$1-5 | 15 min | ✅ Yes | ✅ Network + user | Sensitive data |
| **4: Cloud Armor** | +$10-50 | 30 min | ✅ Yes | ✅ Rate + user | Public APIs |

---

## Quick Start: Enable Security

```bash
# 1. Disable unauthenticated access
gcloud run services update llm-api \
    --no-allow-unauthenticated \
    --region asia-southeast1

# 2. Grant access to your email
gcloud run services add-iam-policy-binding llm-api \
    --member=user:your-email@example.com \
    --role=roles/run.invoker \
    --region asia-southeast1

# 3. Test with token
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" \
    https://your-url/v1/models
```

---

## Architecture: IAM + Identity Tokens

### How It Works

```
User/App
   ↓
gcloud auth / Google Auth Library
   ↓
Creates Identity Token (JWT signed by Google)
   ↓
Sends request with: Authorization: Bearer {token}
   ↓
Cloud Run verifies token signature
   ↓
Cloud IAM checks if user has roles/run.invoker
   ↓
Request allowed/denied
```

### Key Components

| Component | Purpose | Example |
|-----------|---------|---------|
| **Identity Token** | Cryptographically signed proof of identity | JWT from Google |
| **IAM Binding** | Grants permission to invoke the service | user@example.com → roles/run.invoker |
| **Service Account** | Identity for applications/scripts | llm-client@project.iam.gserviceaccount.com |
| **Audit Logs** | Records all access attempts | Cloud Logging |

---

## Setup Guide

### Step 1: Disable Unauthenticated Access

Once you're confident with authentication, disable public access:

```bash
gcloud run services update llm-api \
    --no-allow-unauthenticated \
    --region asia-southeast1
```

**Verify:**
```bash
gcloud run services describe llm-api \
    --region asia-southeast1 \
    --format='value(status.conditions[name="Ready"].metadata.unauthenticated)'
# Should output: False
```

### Step 2: Grant Access to Users

#### For Individual Users

```bash
gcloud run services add-iam-policy-binding llm-api \
    --member=user:teammate@example.com \
    --role=roles/run.invoker \
    --region asia-southeast1
```

#### For Multiple Users

```bash
# Create file: team-members.txt
user:alice@example.com
user:bob@example.com
user:carol@example.com

# Grant all at once
for member in $(cat team-members.txt); do
    gcloud run services add-iam-policy-binding llm-api \
        --member=$member \
        --role=roles/run.invoker \
        --region asia-southeast1
done
```

### Step 3: Grant Access to Service Accounts (for Apps)

For applications that need to access the API:

```bash
# Create service account
gcloud iam service-accounts create llm-client \
    --display-name="LLM API Client"

# Grant it access to the service
gcloud run services add-iam-policy-binding llm-api \
    --member=serviceAccount:llm-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
    --role=roles/run.invoker \
    --region asia-southeast1

# Create and download key (if needed for external apps)
gcloud iam service-accounts keys create llm-client-key.json \
    --iam-account=llm-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com
```

---

## Authentication Methods

### Method 1: Command Line (gcloud)

**For testing and scripts:**

```bash
# One-time setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Get token (valid for 1 hour)
TOKEN=$(gcloud auth print-identity-token)

# Use in requests
curl -H "Authorization: Bearer $TOKEN" \
    https://your-url/v1/chat/completions \
    -d '{"model":"qwen3-8b-awq","messages":[...]}'
```

### Method 2: Python (google-auth library)

**Automatic token refresh with OpenAI SDK:**

```python
import google.auth
from google.auth.transport.requests import Request
from openai import OpenAI

# Get credentials (uses ~/.config/gcloud/application_default_credentials.json)
credentials, project_id = google.auth.default()

# Refresh to ensure valid token
credentials.refresh(Request())

# Use with OpenAI SDK
client = OpenAI(
    base_url="https://llm-api-YOUR_ID.asia-southeast1.run.app/v1",
    api_key="dummy",
    default_headers={"Authorization": f"Bearer {credentials.id_token}"}
)

# Tokens auto-refresh on expiry
response = client.chat.completions.create(
    model="qwen3-8b-awq",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

### Method 3: Service Account Key (External Apps)

**For apps outside Google Cloud:**

```python
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from openai import OpenAI

# Load service account key
SERVICE_ACCOUNT_FILE = "llm-client-key.json"
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Create identity token
credentials.refresh(Request())
identity_token = credentials.id_token

# Use with API
client = OpenAI(
    base_url="https://llm-api-YOUR_ID.asia-southeast1.run.app/v1",
    api_key="dummy",
    default_headers={"Authorization": f"Bearer {identity_token}"}
)
```

### Method 4: Environment Variable

**For containerized apps:**

```bash
# In Cloud Run environment or Docker container
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/llm-client-key.json

# Python code automatically uses this
import google.auth
credentials, _ = google.auth.default()
```

---

## Access Management

### View Current Access

```bash
# See all IAM bindings
gcloud run services get-iam-policy llm-api \
    --region asia-southeast1

# Example output:
# - roles/run.invoker:
#   - user:alice@example.com
#   - user:bob@example.com
#   - serviceAccount:llm-client@project.iam.gserviceaccount.com
```

### Revoke Access

```bash
# Remove a user
gcloud run services remove-iam-policy-binding llm-api \
    --member=user:bob@example.com \
    --role=roles/run.invoker \
    --region asia-southeast1

# Remove a service account
gcloud run services remove-iam-policy-binding llm-api \
    --member=serviceAccount:llm-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
    --role=roles/run.invoker \
    --region asia-southeast1
```

### Rotate Service Account Keys

```bash
# List all keys
gcloud iam service-accounts keys list \
    --iam-account=llm-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Create new key
gcloud iam service-accounts keys create llm-client-key-v2.json \
    --iam-account=llm-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Delete old key (get key ID from list above)
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=llm-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com
```

---

## Monitoring & Audit Logging

### View Access Logs

```bash
# See all API requests
gcloud run services logs read llm-api \
    --region asia-southeast1 \
    --limit 100

# Search for specific user
gcloud run services logs read llm-api \
    --region asia-southeast1 \
    --limit 100 \
    | grep "alice@example.com"

# View detailed audit logs
gcloud logging read \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="llm-api"' \
    --limit 50 \
    --format=json
```

### Set Up Alerts

In Google Cloud Console:

1. Go to **Monitoring → Alert Policies**
2. Create new policy with:
   - **Metric**: Cloud Run service HTTP request count
   - **Condition**: error_count > 10 in 5 minutes
   - **Notification**: Send email/Slack/webhook

### Audit Failed Access

```bash
# View failed authentication attempts
gcloud logging read \
    'resource.type="api" AND severity="ERROR" AND labels.service_name="run.googleapis.com"' \
    --limit 100 \
    --format=json
```

---

## Best Practices

### 1. Principle of Least Privilege

```bash
# CORRECT: Grant specific users/apps only what they need
gcloud run services add-iam-policy-binding llm-api \
    --member=user:alice@example.com \
    --role=roles/run.invoker  # Can only invoke, not deploy or modify

# INCORRECT: Avoid granting broad roles
# Don't use: roles/editor, roles/owner, roles/run.admin
```

### 2. Use Service Accounts for Apps

```bash
# CORRECT: Apps use dedicated service account
gcloud iam service-accounts create llm-inference-app
gcloud run services add-iam-policy-binding llm-api \
    --member=serviceAccount:llm-inference-app@project.iam.gserviceaccount.com \
    --role=roles/run.invoker

# INCORRECT: Don't share user credentials or keys
# Don't hardcode user passwords or personal credentials
```

### 3. Rotate Service Account Keys

```bash
# CORRECT: Rotate keys every 90 days
# Create new key, update app config, delete old key

# Check for old keys
gcloud iam service-accounts keys list \
    --iam-account=llm-client@project.iam.gserviceaccount.com \
    --filter="validAfterTime.date < -P90D"
```

### 4. Regular Audit

```bash
# CORRECT: Regularly review who has access
gcloud run services get-iam-policy llm-api --region asia-southeast1

# Remove users who no longer need access
# Periodically verify: "Who needs access to this API?"
```

### 5. Secure Key Storage

```bash
# CORRECT: Use Google Cloud Secret Manager for keys
gcloud secrets create llm-client-key \
    --replication-policy="automatic" \
    --data-file=llm-client-key.json

# INCORRECT: Never commit keys to git
# Don't: git add llm-client-key.json
# Do: echo "llm-*-key.json" >> .gitignore
```

---

## Troubleshooting

### "Permission denied" Error

```bash
# Check if user is granted access
gcloud run services get-iam-policy llm-api --region asia-southeast1

# Grant access
gcloud run services add-iam-policy-binding llm-api \
    --member=user:your-email@example.com \
    --role=roles/run.invoker \
    --region asia-southeast1

# Give IAM permissions time to propagate (~30 seconds)
```

### "Invalid token" Error

```bash
# Token may be expired - refresh it
TOKEN=$(gcloud auth print-identity-token)

# Or in Python:
from google.auth.transport.requests import Request
credentials.refresh(Request())
```

### Service Account Can't Access Service

```bash
# Check service account has Cloud Run invoker role
gcloud run services get-iam-policy llm-api --region asia-southeast1

# If missing, grant access
gcloud run services add-iam-policy-binding llm-api \
    --member=serviceAccount:your-account@project.iam.gserviceaccount.com \
    --role=roles/run.invoker \
    --region asia-southeast1

# Verify the service account name is correct
gcloud iam service-accounts list
```

---

## Migration Guide

### From Unauthenticated to Authenticated

**Without downtime:**

```bash
# 1. Keep current unauthenticated access
# (Users can still use without tokens)

# 2. Grant IAM access to all current users
for user in alice@ex.com bob@ex.com carol@ex.com; do
    gcloud run services add-iam-policy-binding llm-api \
        --member=user:$user \
        --role=roles/run.invoker \
        --region asia-southeast1
done

# 3. Update client code to use tokens (no rush)

# 4. Once all clients updated, disable unauthenticated access
gcloud run services update llm-api \
    --no-allow-unauthenticated \
    --region asia-southeast1
```

---

## Additional Resources

- [Google Cloud Run Security](https://cloud.google.com/run/docs/securing/authenticating/overview)
- [Identity-Based Access Control](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Service Accounts Best Practices](https://cloud.google.com/iam/docs/service-accounts-manage)
- [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit)
