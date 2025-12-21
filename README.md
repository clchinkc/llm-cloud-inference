# LLM Cloud Inference

OpenAI-compatible LLM API using vLLM to serve Qwen3-8B-AWQ (4-bit quantized) on Google Cloud Run with GPU support.

Self-hosted deployment with vLLM inference engine and Qwen3. Scales to zero when idle. ~80ms latency when warm.

## Features

- OpenAI-compatible API - Same interface as OpenAI SDK
- Scale-to-zero - $0/month when idle
- vLLM v0.8.4 - Single-process engine (stable on Cloud Run)
- Qwen3-8B-AWQ - 8B parameter model with 4-bit quantization
- 80% GPU utilization, 64 concurrent sequences
- Streaming responses supported
- ~80ms latency (warm), ~43 tokens/sec throughput

## Quick Start

### Prerequisites
Before you start, verify you have:
- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated: `gcloud auth login`
- Docker installed
- ~50GB free disk space (for model download)

### Cloud Build (Recommended - Automated)

For **automatic deployment on every push to main**:

1. Setup Cloud Build trigger (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete setup)
2. Push code to main branch
3. Cloud Build automatically:
   - Builds Docker image (~15 mins)
   - Pushes to Artifact Registry (~2 mins)
   - Deploys to Cloud Run (~10 mins)
4. Service is live with scale-to-zero (min-instances=0)

**Features:**
- ✅ **Fully automated** - no manual intervention after setup
- ✅ **Scale-to-zero** - $0/month when idle
- ✅ **Fast responses** - ~80ms latency when warm
- ✅ **Cost efficient** - only pay for GPU when processing requests

**Cost**: $0.06 per build + ~$0.90/hour when running (GPU charges only during active requests)

### Manual Deployment

For one-time or testing deployments:

```bash
# 1. Set your GCP project
export GCP_PROJECT_ID="your-project-id"

# 2. Setup GCP resources (APIs, service account, bucket)
make setup                    # ~2 min

# 3. Download and upload model to GCS
make download-model           # ~10 min (8GB download)
make upload-model             # ~5 min

# 4. Deploy to Cloud Run
gcloud builds submit --config=cloudbuild.yaml    # ~15-20 min

# 5. Test the API
make test                     # ~5 min (cold start)
```

**Total time: ~35-40 minutes first deployment**

Endpoint deployed with IAM security enabled by default.

**After deployment:**
1. First request: ~4-5 minutes (model loads from GCS)
2. Warm requests: ~80ms latency
3. Idle scale-down: ~2-3 minutes after last request
4. Grant access: `./scripts/security_setup.sh grant-user email@example.com`

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed guide.

---

## Grant Access to Team Members

Deployment is secure by default - only authorized users can access it.

To grant access to team members:

```bash
# Grant access to a user
./scripts/security_setup.sh grant-user teammate@example.com

# View who has access
./scripts/security_setup.sh list-access

# Remove access
./scripts/security_setup.sh revoke-user teammate@example.com
```

**For service accounts or applications**, see [docs/SECURITY.md](docs/SECURITY.md).

---

## 💬 Using the API

### Option 1: Use an Existing Deployed Endpoint (Recommended for Most Users)

If someone has already deployed this and shared their endpoint:

```bash
# Example: They give you this URL
export LLM_API_URL="https://llm-api-abc123xyz.asia-southeast1.run.app"
```

Then skip to the usage examples below.

---

### Option 2: Deploy Your Own (For Full Control)

Deploy your own private endpoint:

```bash
export GCP_PROJECT_ID="your-project"
make setup && make download-model && make upload-model && make deploy

# Then get your URL:
gcloud run services describe llm-api --region asia-southeast1 --format 'value(status.url)'
```

---

## Using the API

### Quick Start (Scripts)

The scripts auto-detect your service URL. Just run them directly:

```bash
# Python + OpenAI SDK (auto-detects service URL)
python3 scripts/example_usage.py

# Interactive chatbot
python3 scripts/chat.py

# Benchmark latency
python3 scripts/benchmark_latency.py
```

Alternatively, set the environment variable explicitly:
```bash
export LLM_API_URL="https://llm-api-YOUR_ID.asia-southeast1.run.app"
python3 scripts/example_usage.py
```

Or retrieve your service URL:
```bash
gcloud run services describe llm-api --region asia-southeast1 --format 'value(status.url)'
```

See [scripts/](scripts/) directory for examples. Full documentation in [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).

### Direct API Usage

**cURL:**
```bash
curl -X POST "https://your-url/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-8b-awq","messages":[{"role":"user","content":"Hello!"}],"max_tokens":100}'
```

See [docs/SECURITY.md](docs/SECURITY.md) for authentication details and [scripts/example_usage.py](scripts/example_usage.py) for Python SDK examples.

## Performance

### Latency & Throughput (Warm Instance)

| Metric | Self-Hosted |
|--------|-------------|
| **TTFT** (p50) | ~80ms |
| **Cost/1K tokens** | ~$0.005 |
| **Throughput** | ~43 tokens/sec |

### Cold Start

| Deployment | Cold Start | Cost |
|-----------|-----------|------|
| **Standard** (GCS download) | ~4-5 minutes | $0 idle, $0.90/hr active |
| **Always-Warm** (min_instances=1) | 0 seconds | ~$650/month |

See [docs/BENCHMARKS.md](docs/BENCHMARKS.md) for detailed performance analysis.

## Cost Breakdown

### Monthly Cost Examples

| Usage | Scale-to-Zero | Always-Warm |
|-------|---------------|-------------|
| Idle | $0 | $648 |
| 10 hours/month | $9 | $648 |
| 100 hours/month | $90 | $648 |
| 1000 hours/month | $900 | $648 |

Self-hosted scales to zero, providing cost savings for low-usage and intermittent workloads.

### GPU Pricing (L4 @ $0.90/hour)

```
1 hour:   $0.90
1 day:    $21.60
1 month:  ~$648
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `qwen3-8b-awq` | Model to deploy |
| `GCS_BUCKET` | `{project}-models` | GCS bucket for model storage |
| `GPU_MEMORY_UTIL` | `0.80` | GPU memory usage (80% = 16.8GB of 24GB) |
| `MAX_MODEL_LEN` | `8192` | Max context window (tokens) |
| `MAX_NUM_SEQS` | `64` | Max concurrent sequences |

## Documentation

- [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) - Deployment guide
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment options
- [docs/SECURITY.md](docs/SECURITY.md) - IAM + identity token authentication
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [docs/BENCHMARKS.md](docs/BENCHMARKS.md) - Performance metrics
- [docs/V1_ENGINE_ANALYSIS.md](docs/V1_ENGINE_ANALYSIS.md) - vLLM v0.8.4 rationale
- [CHANGELOG.md](CHANGELOG.md) - Version history

## Makefile Commands

```bash
# Setup
make setup              # Setup GCP project and resources
make download-model     # Download model from Hugging Face
make upload-model       # Upload model to GCS

# Deployment
make build              # Build Docker container
make deploy             # Deploy to Cloud Run
make deploy-baked       # Deploy with model baked in image
make test               # Test the deployed API

# Security
./scripts/security_setup.sh quick-setup   # Enable authentication + create service account
./scripts/security_setup.sh grant-user    # Grant access to a user
./scripts/security_setup.sh list-access   # View who has access

# Usage
make chat               # Interactive CLI chatbot
make example            # Run example scripts
make benchmark          # Run latency benchmarks
make logs               # View Cloud Run logs
```

## Model: Qwen3-8B-AWQ

- Name: Qwen3-8B-AWQ
- License: Apache 2.0
- Size: 8 billion parameters
- Quantization: 4-bit AWQ (75% size reduction from FP16)
- Context window: 8,192 tokens
- Capabilities: Reasoning mode, multilingual, code generation

## Troubleshooting

### Cold Start Too Slow?

For faster responses at higher cost, enable always-warm deployment:
```bash
gcloud run services update llm-api --min-instances 1 --region asia-southeast1
```

To return to scale-to-zero (default, lower cost):
```bash
gcloud run services update llm-api --min-instances 0 --region asia-southeast1
```

### Out of Memory?

Reduce GPU memory utilization in `docker/startup.sh`:
```bash
--gpu-memory-utilization 0.70  # Change from 0.80
```

### API Not Responding?

Check logs:
```bash
make logs
```

Look for errors in Container startup phase.

## Security

Default: All deployments use IAM + Identity Tokens. No API keys, no secret management.

Automatic Setup: Cloud Build deployment automatically:
- Disables unauthenticated access
- Creates service account for applications
- Sets up IAM bindings

**Granting Access**:
```bash
# Grant team member access
./scripts/security_setup.sh grant-user email@example.com

# View who has access
./scripts/security_setup.sh list-access

# Test authentication
./scripts/security_setup.sh test-auth
```

**Authenticate Requests** (Python):

See [scripts/example_usage.py](scripts/example_usage.py) for the complete working implementation using the `AuthenticatedOpenAI` class.

Quick usage:
```bash
python scripts/example_usage.py     # Complete example
python scripts/chat.py              # Interactive chat
python scripts/quick_test.py        # Test with cold-start handling
```

The scripts automatically handle Google Cloud identity token authentication using httpx event hooks.

See [docs/SECURITY.md](docs/SECURITY.md) for:
- 4 security level options (development, production, enterprise)
- Complete authentication methods (Python, cURL, Bash, service accounts)
- Key management and best practices

## Monitoring

View logs:
```bash
make logs
```

Set up alerts (in Cloud Console):
- Error rate > 5%
- Response time > 10s
- GPU memory > 90%

## Contributing

Reference implementation. Feel free to:
- Report issues on GitHub
- Submit improvements
- Adapt for your use case

## License

MIT - See [LICENSE](LICENSE) file

## FAQ

**Q: Why vLLM v0.8.4 instead of latest?**
A: v0.9.0+ uses multiprocess architecture that fails silently in Cloud Run. See [docs/V1_ENGINE_ANALYSIS.md](docs/V1_ENGINE_ANALYSIS.md).

**Q: Can I use a different model?**
A: Set `MODEL_NAME` and upload to GCS. Requires GPU with enough VRAM.

**Q: How do I reduce costs?**
A: Use scale-to-zero (min_instances=0) or reduce GPU_MEMORY_UTIL.

**Q: Is this stable?**
A: Deployed and tested on Cloud Run with vLLM v0.8.4.

---

**Get started now**: `export GCP_PROJECT_ID=your-project && make setup`
