# Deployment

## Prerequisites

- Google Cloud account with billing
- `gcloud` CLI authenticated
- Docker installed
- Python 3.10+

## Steps

```bash
# 1. Set project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# 2. Setup GCP resources
make setup

# 3. Download model
make download-model

# 4. Upload to GCS
make upload-model

# 5. Deploy
make deploy

# 6. Test
make test
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `qwen3-8b-awq` | Model name |
| `GCS_BUCKET` | `{project}-models` | GCS bucket |
| `PORT` | `8080` | Server port |
| `GPU_MEMORY_UTIL` | `0.80` | GPU memory usage (optimized for stability) |
| `MAX_MODEL_LEN` | `8192` | Max context length |
| `MAX_NUM_SEQS` | `64` | Max concurrent sequences |

## Deployment Notes

**Current Version:** vLLM v0.8.4 (proven stable, recommended for Cloud Run)

The deployment uses v0.8.4 instead of the latest vLLM version because:
- V1 engine (v0.9+) uses multiprocess architecture that fails silently in Cloud Run
- V0 engine provides clear error logging and reliable startup
- All Qwen3 features work correctly with v0.8.4

**Performance Targets:**
- Cold start: ~4-5 minutes (first request from idle)
- Warm response: <100ms latency
- Throughput: ~40-50 tokens/second
- GPU memory: 80% utilization (16.8GB of 24GB L4)

## Deployment Options

### Standard Deployment (Recommended)

Downloads model from GCS on first startup. Best for cost-efficiency with scale-to-zero.

```bash
make deploy
```

**Cost:** $0 when idle, ~$0.90/hour when active

### Baked Image Deployment

Pre-bakes the model into Docker image for slightly faster first startup (reduces download time).

```bash
make deploy-baked
```

**Trade-offs:**
- Image size: ~10GB (vs ~1GB for standard)
- Image build: ~10 minutes
- Cold start: Marginal improvement due to model loading, not download

### Always-Warm Deployment

```bash
gcloud run services update llm-api --region asia-southeast1 --min-instances 1
```

Cost: ~$650/month but zero cold start.

## Operational Timing Reference

### Cold Start Duration

**First request timeline** (service at 0 instances):

| Phase | Duration | Notes |
|-------|----------|-------|
| Container initialization | 5-30s | Download and start container |
| Model download from GCS | 2-3 min | ~4GB of model weights |
| Model GPU initialization | 1-2 min | Load into VRAM, warmup |
| **Total** | **4-5 min** | Standard deployment |

**Important**: Cold starts happen ~2-3 minutes after scale-down completes, not immediately. The service keeps a brief warm period after last request.

### Idle & Scale-Down Timeline

**With `min_instances=0` (default, recommended)**:

| Event | Time After Last Request | Status |
|-------|------------------------|--------|
| Last request completes | 0 sec | Billing: $0.90/hr active |
| Grace period begins | 0 sec | Service stays warm |
| Idle grace period | ~1-2 min | Instance still running, GPU still billing |
| Container cleanup | ~30-60 sec | System prepares shutdown |
| **Scale-down complete** | **~2-3 min** | Billing stops ($0/month) |

**Example cost**:
- One request takes 5 minutes (2-3 min idle) = ~$0.04

### Client Timeout Recommendation

**Always set client timeout ≥ 5 minutes** for cold starts:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-url/v1",
    api_key="dummy",
    timeout=300,  # 5 minutes for cold start
)
```

Without this, requests will timeout during cold start.

## Troubleshooting

**Cold start slow**: This is normal (4-5 minutes). Use `min-instances=1` for always-warm if you need instant responses.

**Cold start timeout**: Increase client timeout to 5+ minutes, or set `min-instances=1`.

**Out of memory**: Reduce `GPU_MEMORY_UTIL` or `MAX_MODEL_LEN`

**Auth issues**: Check service account has `roles/storage.objectViewer`

**Unexpected costs**: Verify `min_instances=0` is set (scale-to-zero)
