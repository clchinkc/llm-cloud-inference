# Deployment Guide

Deploy vLLM to Google Cloud Run using Cloud Build for automated CI/CD.

## Current Configuration

- **Region:** asia-southeast1 (nvidia-l4 GPU support)
- **GPU:** nvidia-l4 (24GB VRAM)
- **Model:** Qwen3-8B-AWQ (4-bit quantized)
- **Deployment:** Fully automated via Cloud Build on every push to main
- **Security:** IAM-authenticated by default (unauthenticated access disabled)
- **Scale:** min-instances=0 (scales to zero when idle, $0/month cost)

---

## Quick Start (Cloud Build - Recommended)

**Automatic deployment on every push to `main` branch**

Two options for automatic deployment:
1. **Cloud Build GitHub webhook** (simpler, no secrets needed) - Automatically triggered by GitHub
2. **GitHub Actions** (more control) - GitHub Actions triggers Cloud Build deployment

### Prerequisites

- Google Cloud Project with Cloud Build, Cloud Run, Artifact Registry enabled
- GitHub repository connected to Cloud Build
- GCS bucket for model storage: `gs://PROJECT_ID-models/`

### Option 1: Cloud Build GitHub Webhook (Automatic)

No additional setup needed - the Cloud Build trigger is already connected and will automatically deploy on every push to `main`.

### Option 2: GitHub Actions (with GCP Credentials)

If you want GitHub Actions to trigger the deployment:

1. Create a GCP service account key:
```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=llm-inference@llm-inference-31155.iam.gserviceaccount.com
```

2. Add the key to GitHub Secrets:
   - Go to GitHub → Settings → Secrets and variables → Actions
   - Create new secret named `GCP_SA_KEY`
   - Paste the contents of `key.json`
   - Delete the local `key.json` file

3. GitHub Actions will now automatically trigger Cloud Build on every push to `main`

### Setup (5 minutes)

**1. Create GCS bucket:**
```bash
gsutil mb gs://YOUR_PROJECT_ID-models/
```

**2. Upload model to GCS:**
```bash
# Download model locally
python scripts/download_and_quantize.py

# Upload to GCS
gsutil -m cp -r models/qwen3-8b-awq gs://YOUR_PROJECT_ID-models/
```

**3. Connect GitHub to Cloud Build:**
Go to Google Cloud Console → Cloud Build → Settings → Connect Repository

**4. Create build trigger:**
```bash
gcloud builds triggers create github \
  --repo-name=llm-cloud-inference \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern=main \
  --build-config=cloudbuild.yaml
```

**Done!** Now every push to `main` automatically builds and deploys.

---

## How It Works

### Current Deployment Strategy

**Configuration:**
- `min-instances=0`: Scale-to-zero when idle, $0 cost when not in use
- `docker/Dockerfile`: Downloads model from GCS on first startup
- `cloudbuild.yaml`: Automated build, push, deploy on every push to main

**Performance:**
- **First request (cold start):** ~4-5 minutes (container startup + model download from GCS)
- **Warm requests:** ~80ms latency
- **Cost:** $0 when idle, ~$0.90/hour when processing (L4 GPU only)

**Why This Approach:**
1. **Fully automated** - Push to main → Auto-deployed via Cloud Build
2. **Cost-efficient** - Scale-to-zero saves money when service is idle
3. **Simple** - Standard Docker approach, easy to modify
4. **Best for infrequent usage** - Minimal costs for low-traffic scenarios

**Deployment Flow:**
```

---

## Automated Deployment Workflow

**Once Cloud Build trigger is created, everything is automated:**

```
Your local machine:
  git push origin main
    ↓
GitHub webhook triggers Cloud Build
    ↓
Cloud Build:
  - Build Docker image (~15 mins)
  - Push to Artifact Registry (~2 mins)
  - Deploy to Cloud Run with min-instances=0 (~10 mins)
    ↓
Service is live (~25-30 mins total)
```

**First Request After Deployment:**
- Container cold-starts: ~30 seconds
- Model downloads from GCS: ~3-4 minutes
- Total first request: ~4-5 minutes

**Subsequent Requests:**
- ~80ms latency when service is warm
- Service scales to zero after idle period

**Cost Breakdown:**
- Cloud Build: $0.06 per build
- Cloud Run: $0.90/hour when running (GPU charges only during active requests)
- Idle: $0/month
- GCS storage for model: ~$0.12-0.18/month

---

## Manual Deployment (Single Command)

If you want to deploy without waiting for Cloud Build:

```bash
gcloud builds submit --region=asia-southeast1 --config=cloudbuild.yaml
```

This runs the same cloudbuild.yaml locally, building and deploying directly.

---

## Monitoring Deployments

**View build logs:**
```bash
gcloud builds log COMMIT_SHA --stream
```

**View Cloud Run logs:**
```bash
gcloud run services logs read llm-api --region asia-southeast1 --limit 50
```

**Check service status:**
```bash
gcloud run services describe llm-api --region asia-southeast1
```

---

## Cost Examples

### Low Usage (1 request per day)
```
Cloud Build: $1.80 (30 builds/month × $0.06)
Cloud Run:   $0.09 (1 min/day × $0.90/hour ≈ $2.70/month)
GCS storage: $0.15
Total:       ~$2/month
```

### Medium Usage (10 requests per day, 2 hours/month active)
```
Cloud Build: $1.80 (30 builds/month)
Cloud Run:   $1.80 (2 hours × $0.90/hour)
GCS storage: $0.15
Total:       ~$3.75/month
```

### High Usage (100 hours/month active)
```
Cloud Build: $1.80 (30 builds/month)
Cloud Run:   $90 (100 hours × $0.90/hour)
GCS storage: $0.15
Total:       ~$92/month
```

---

## Troubleshooting

**Build fails with "disk space":**
- Cloud Build already has large machine type configured
- If still failing, increase timeout in cloudbuild.yaml

**Deployment doesn't auto-trigger:**
- Verify GitHub connection in Cloud Build Settings
- Check trigger matches your branch (default: main)

**Cold start is slow (4-5 minutes):**
- First request after scale-down is slower due to:
  1. Container startup: ~30 seconds
  2. Model download from GCS: ~3-4 minutes
- This is expected and normal with scale-to-zero
- To reduce cold-start time, enable always-warm:
  ```bash
  gcloud run services update llm-api --min-instances 1 --region asia-southeast1
  ```

**GCS FUSE mounting fails:**
- Verify service account has `roles/storage.objectViewer` on GCS bucket
- Check bucket name matches environment variable

---

## Next Steps

1. Complete Cloud Build setup (see Quick Start)
2. Push code to `main` branch
3. Watch build progress in Cloud Build console
4. Test deployed service using scripts or curl
5. (Optional) Switch to GCS FUSE for faster updates

---

## Testing the Deployment

### Testing with Authentication (Recommended)

The service is secured by default with IAM authentication. To test:

```bash
# Option 1: Use the example script (auto-detects service URL and gets identity token)
python scripts/example_usage.py

# Option 2: Use the chat script for interactive testing
python scripts/chat.py

# Option 3: Quick test with retry logic for cold starts
python scripts/quick_test.py

# Option 4: Grant access to a user and they can test
./scripts/security_setup.sh grant-user user@example.com
```

**Note:** Scripts default to asia-southeast1 region. To override:
```bash
GCP_REGION=other-region python scripts/example_usage.py
```

### How Authentication Works

The scripts use Google Cloud identity tokens for authentication:

1. **Get identity token:** `gcloud auth print-identity-token`
2. **Pass in request:** `Authorization: Bearer <token>` header
3. **OpenAI SDK:** Custom `AuthenticatedOpenAI` class in scripts handles this automatically

### Granting Access to Team Members

```bash
# Grant access to a user
./scripts/security_setup.sh grant-user teammate@example.com

# View who has access
./scripts/security_setup.sh list-access

# Test your authentication
./scripts/security_setup.sh test-auth
```

For service accounts or applications, see [docs/SECURITY.md](./SECURITY.md).

---

## Reference

- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Run GPU Documentation](https://cloud.google.com/run/docs/configuring/services/gpu)
- [GCS FUSE Documentation](https://cloud.google.com/storage/docs/gcs-fuse)
