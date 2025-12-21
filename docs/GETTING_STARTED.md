# Getting Started: Deploy Your Own LLM on Cloud Run

This guide walks you through deploying a production-ready LLM API on Google Cloud Run in 15-20 minutes.

## Prerequisites

1. **Google Cloud Account**
   - Create one at https://console.cloud.google.com
   - Enable billing (free tier doesn't include GPU)
   - Note your project ID

2. **Local Tools**
   - `gcloud` CLI: https://cloud.google.com/sdk/docs/install
   - Docker: https://docs.docker.com/get-docker/
   - Python 3.10+: https://www.python.org/downloads/

3. **System Requirements**
   - 50GB free disk space (for model download)
   - Internet connection
   - ~10 minutes for initial setup

## Step 1: Authenticate with GCP

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
export GCP_PROJECT_ID="your-actual-project-id"
gcloud config set project $GCP_PROJECT_ID

# Verify
gcloud config get-value project
```

## Step 2: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/llm-cloud-inference.git
cd llm-cloud-inference

# Set environment variable
export GCP_PROJECT_ID="your-actual-project-id"
```

## Step 3: Setup GCP Resources

```bash
# This enables required APIs, creates service account, and sets up GCS bucket
make setup
```

**What this does:**
- Enables Cloud Run, Container Registry, and Cloud Storage APIs
- Creates a GCS bucket for model storage
- Creates a service account with storage permissions
- Sets up billing alerts at $50 (optional)

**Time: ~2 minutes**

## Step 4: Download the Model

```bash
# Download Qwen3-8B-AWQ from Hugging Face (~8GB)
make download-model
```

**What this does:**
- Downloads model from Hugging Face Hub
- Saves to `./models/qwen3-8b-awq/`
- Requires Hugging Face account (free)

**Time: ~5-10 minutes** (depends on internet speed)

**Troubleshooting:**
- If download fails, try: `huggingface-cli login` first
- Requires 15GB free disk space
- Can run in background with `make download-model &`

## Step 5: Upload Model to GCS

```bash
# Upload model to GCS bucket
make upload-model
```

**What this does:**
- Uploads ~4GB of model files to Google Cloud Storage
- Makes model accessible from Cloud Run

**Time: ~3-5 minutes**

## Step 6: Build and Deploy

```bash
# Build Docker container and deploy to Cloud Run
make deploy
```

**What this does:**
- Builds Docker image with vLLM and dependencies
- Pushes image to Google Container Registry
- Deploys to Cloud Run with GPU
- Sets up startup probes for reliable container startup
- Creates endpoint URL

**Time: ~5-10 minutes**

**First deployment output:**
```
=== Deployed ===
URL: https://llm-api-abc123def456.asia-southeast1.run.app
```

Save this URL - you'll need it to use the API!

## Step 7: Test the API

```bash
# Quick test
make test
```

**Expected output:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "qwen3-8b-awq",
      "object": "model",
      "owned_by": "Qwen",
      "permission": [],
      "root": "qwen3-8b-awq",
      "parent": null
    }
  ]
}
```

**Troubleshooting:**
- If timeout: Service is cold-starting, wait 5-10 minutes and try again
- Check logs: `make logs`
- Verify endpoint: `gcloud run services list --region asia-southeast1`

## Understanding Cold Start & Idle Behavior

### Cold Start Timeline

When you make the **first request** to an idle service:

```
Request sent
    ↓ (0 seconds)
Container initializes
    ↓ (5-30 seconds) - Container startup, downloading Docker image
Model loads from GCS
    ↓ (2-3 minutes) - Downloading ~4GB model from storage
Model initializes in GPU memory
    ↓ (1-2 minutes) - Preparing model, warmup, allocating VRAM
vLLM server ready
    ↓ (0 seconds)
First response received
    ↓ (240+ seconds total)
```

**Total First Start: 4-5 minutes**

**What you see:**
- Request may timeout if client timeout < 5 minutes
- Cloud Run startup probe allows up to 4 minutes for startup
- After startup completes, all requests are fast (~80ms)

**Example timeline:**
```
12:00:00 - First request arrives (service has 0 instances)
12:00:05 - Container downloaded and starting
12:00:30 - Container running, model download begins
12:03:00 - Model fully downloaded from GCS
12:04:00 - Model loaded into GPU, server ready
12:04:30 - First response sent to client
```

### Idle Scaling (Scale-to-Zero)

With `min_instances=0` (default, recommended for cost):

```
Last request completes
    ↓ (1-2 minutes)
No new requests arrive
    ↓
Container keeps running (brief grace period)
    ↓ (1-2 minutes total idle time)
Cloud Run terminates instance
    ↓ (billing stops)
Service now at 0 instances = $0/month
```

**Important timings:**
- **Idle grace period**: ~1-2 minutes after last request
- **Container cleanup**: ~30-60 seconds
- **Total idle time before shutdown**: ~2-3 minutes
- **Cost stops**: Immediately after instance terminates

**Example cost scenario:**
```
12:00:00 - Make request, instance 1 starts ($0.90/hr)
12:04:30 - Response received (instance still $0.90/hr)
12:05:30 - Idle for 1 minute (still running)
12:06:00 - Idle for 1.5 minutes (still running)
12:07:00 - Idle for 2.5 minutes → Instance terminates
12:07:00 - Billing stops ($0/month)

Total cost for this session: ~$0.04 (6+ minutes of GPU time)
```

### Warm Instance (Always-On)

With `min_instances=1`:

```
Service always running (1 instance minimum)
    ↓
Every request: Fast response (~80ms)
    ↓
24/7 continuous billing: $0.90/hour × 24 × 30 = ~$648/month
    ↓
No cold starts (instant responses)
```

**Cost tradeoff:**
- Standard: $0 idle + $0.90/hr active = cheap
- Always-warm: $648/month = expensive but instant

## Step 8: Grant Access to Team Members (If Shared Deployment)

### Automatic Security Setup

During deployment, the GitHub Actions workflow automatically:
- ✅ Disables unauthenticated access
- ✅ Creates a service account (`llm-client`) for applications
- ✅ Sets up IAM bindings for the service account

**Your deployment is secure by default** - only users you authorize can access it.

### Grant Access to a User

If you want to share the API with team members:

```bash
# Replace with their email
gcloud run services add-iam-policy-binding llm-api \
    --member=user:teammate@example.com \
    --role=roles/run.invoker \
    --region asia-southeast1 \
    --project $GCP_PROJECT_ID
```

**No need for .env files or GitHub secrets** - IAM handles access control automatically.

### Grant Access to a Service Account (for Apps)

If an application needs to access the API:

```bash
# Create a service account for the app
gcloud iam service-accounts create my-app \
    --display-name="My Application"

# Grant it access
gcloud run services add-iam-policy-binding llm-api \
    --member=serviceAccount:my-app@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
    --role=roles/run.invoker \
    --region asia-southeast1
```

### View Who Has Access

```bash
gcloud run services get-iam-policy llm-api --region asia-southeast1
```

### Revoke Access

```bash
gcloud run services remove-iam-policy-binding llm-api \
    --member=user:teammate@example.com \
    --role=roles/run.invoker \
    --region asia-southeast1
```

See [docs/SECURITY.md](SECURITY.md) for detailed authentication methods (Python, cURL, Bash scripts).

---

## Step 9: Use the API

### Get Your URL

```bash
# Save your endpoint URL
export LLM_API_URL=$(gcloud run services describe llm-api \
  --region asia-southeast1 \
  --format 'value(status.url)')

echo $LLM_API_URL
```

### Run Example Scripts

**Python (OpenAI SDK):**
```bash
export LLM_API_URL="https://your-url"
python3 scripts/example_usage.py
```
See [scripts/example_usage.py](../scripts/example_usage.py) for code.

**Interactive Chatbot:**
```bash
export LLM_API_URL="https://your-url"
python3 scripts/chat.py
```
Chat in real-time with the model!

**Benchmarking:**
```bash
export LLM_API_URL="https://your-url"
python3 scripts/benchmark_latency.py
```
Measure latency and throughput.

### With Authentication (if access is restricted)

If the deployment has IAM enabled and you don't have direct access yet:

```bash
# Get your identity token
TOKEN=$(gcloud auth print-identity-token)

# Make request with authentication
curl -X POST "$LLM_API_URL/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-8b-awq",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }' | jq .
```

## Understanding Costs

### Cold Start (First Request)

- Initial: 0-5 minutes to initialize
- Happens when service has 0 instances running
- One time per cold start, not per request

**Cost**: GPU time only = ~$0.01-0.08 (varies by region)

### Warm Instance (After First Request)

- <100ms response latency
- Cheap to keep running (see below)
- Auto-scales down after inactivity

**Cost**: $0.90/hour when actively processing requests

### Idle Time

- Free! No cost when no requests
- Auto-scaled down to zero instances
- Next request triggers cold start

**Cost**: $0 per hour idle

### Example Costs

```
Development (1 hour/week):
  - 52 hours/year × $0.90 = $46.80/year
  - Plus cold starts: ~$5-10/year
  - Total: ~$50-60/year

Production (100 hours/month):
  - 1,200 hours/year × $0.90 = $1,080/year
  - Plus cold starts: minimal
  - Total: ~$1,080-1,100/year

Commercial API (OpenAI gpt-4o-mini):
  - ~$0.075 per 1K tokens
  - At 100k tokens/month: $7.50/month = $90/year
  - At 1M tokens/month: $75/month = $900/year
```

## Optimization Tips

### Reduce Cold Start Time

```bash
# Keep instance always warm (costs ~$650/month)
gcloud run services update llm-api \
    --min-instances 1 \
    --region asia-southeast1

# To return to scale-to-zero
gcloud run services update llm-api \
    --min-instances 0 \
    --region asia-southeast1
```

### Reduce Memory Usage

Edit `docker/startup.sh` and change:
```bash
--gpu-memory-utilization 0.80  # Reduce from 0.80 to 0.70
```

Then redeploy with `make deploy`.

### Monitor Costs

```bash
# View Cloud Run billing
gcloud billing accounts list

# Set budget alerts in Google Cloud Console
# Navigate to: Billing > Budgets & Alerts > Create Budget
```

## Common Issues and Solutions

### Issue: "Service failed to become healthy"

**Solution:** Wait longer for cold start.
```bash
# Check logs
make logs

# Cold starts take 4-5 minutes for this deployment
# This is normal for vLLM model loading
```

### Issue: "Out of memory" errors

**Solution:** Reduce GPU memory utilization
```bash
# Edit docker/startup.sh
# Change --gpu-memory-utilization 0.80 to 0.70

# Redeploy
make deploy
```

### Issue: "Authentication failed"

**Solution:** Ensure service account has storage permissions
```bash
# Verify service account exists
gcloud iam service-accounts list

# Grant permissions if needed
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:llm-inference@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"
```

### Issue: Model not downloading from GCS

**Solution:** Verify bucket exists and is accessible
```bash
# List GCS buckets
gsutil ls

# Verify model files are present
gsutil ls gs://${GCP_PROJECT_ID}-models/qwen3-8b-awq/
```

## Next Steps

1. **Share with Team** - Grant access to team members using `gcloud run services add-iam-policy-binding` (see Step 8 above)
2. **Integrate with Your App** - Use the Python SDK in your application
3. **Set Up Monitoring** - View Cloud Run logs: `make logs`
4. **Try Different Models** - Edit `MODEL_NAME` in Makefile to try other models
5. **Read Deep Dives** - Check [docs/](.) for architecture, performance, and detailed security information

## Cleanup (Optional)

To remove everything and stop incurring costs:

```bash
# Delete Cloud Run service
gcloud run services delete llm-api --region asia-southeast1 --quiet

# Delete GCS bucket
gsutil -m rm -r gs://${GCP_PROJECT_ID}-models

# Delete service account
gcloud iam service-accounts delete llm-inference@${GCP_PROJECT_ID}.iam.gserviceaccount.com --quiet

# Delete container image
gcloud container images delete gcr.io/${GCP_PROJECT_ID}/llm-cloud-inference:latest --quiet
```

## Support

- **Logs**: `make logs`
- **Service Status**: `gcloud run services list --region asia-southeast1`
- **Documentation**: See [README.md](../README.md) and [docs/](.)
- **Issues**: Check GitHub issues or [V1_ENGINE_ANALYSIS.md](V1_ENGINE_ANALYSIS.md)

---

Your LLM deployment is now live.

For detailed information about performance, architecture, and benchmarks, see the other documentation files in the `docs/` directory.
