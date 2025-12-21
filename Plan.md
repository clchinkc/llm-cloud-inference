---
tags:
  - Project
  - Career
  - LLM
  - Cloud-Infrastructure
  - AI-Engineering
  - Self-Hosting
category: project
type: implementation_guide
status: planning
priority: high
location: at_home
project_type: career
created: 2025-11-26
updated: 2025-12-20
repo_name: llm-cloud-inference
milestones:
  - date: 2025-12-22
    deliverable: "Repository created with project structure"
  - date: 2025-12-28
    deliverable: "GCP project setup with APIs enabled, model uploaded to GCS"
  - date: 2026-01-05
    deliverable: "Dockerfile created and tested locally"
  - date: 2026-01-12
    deliverable: "Deployed on Cloud Run with GPU"
  - date: 2026-01-19
    deliverable: "Latency benchmarks completed (API vs self-hosted)"
  - date: 2026-01-26
    deliverable: "Observability dashboard and cost optimization complete"
success_metrics:
  - "OpenAI-compatible API endpoint accessible from local machine"
  - "Cost-optimized with min_instances=0"
  - "Cold start latency <3 minutes (with quantized model)"
  - "Monthly cost <$50 for light usage"
  - "Latency benchmark report comparing self-hosted vs OpenAI/Anthropic API"
related_knowledge:
  - "[[LLM Application Practical Guidelines]]"
  - "[[RAG Implementation - Retrieval Augmented Generation]]"
  - "[[Commercial-AI-Agent-Development-Guide-从0到1]]"
---

# LLM Hosting Project: OpenAI-Compatible API on Google Cloud Run

**Part of**: Career Development → AI/ML Infrastructure Skills

> **Goal**: Deploy a self-hosted Large Language Model with OpenAI-compatible API endpoints on Google Cloud Run, optimized for cost-efficiency and internet accessibility. Benchmark latency against commercial APIs.

---

## 📋 Project Overview

This project builds hands-on experience with:
- **LLM Deployment**: Production-grade model serving with modern inference engines
- **Cloud Infrastructure**: Google Cloud Run with GPU support
- **API Design**: OpenAI-compatible endpoints
- **Cost Optimization**: Serverless architecture with scale-to-zero
- **Performance Engineering**: Latency benchmarking and optimization

### Why This Matters for Career

1. **High-Demand Skills**: LLM deployment is a critical skill for AI/ML engineers
2. **Portfolio Project**: Demonstrates end-to-end infrastructure capabilities
3. **Practical Experience**: Real-world cost optimization and performance tuning
4. **Interview Ready**: Concrete experience to discuss in technical interviews
5. **Benchmarking Expertise**: Understanding latency trade-offs is key for production systems

---

## 🗂️ Repository Structure & Naming

### Repository Name: `llm-cloud-inference`

Rationale: Clear, descriptive, and follows conventions for cloud-deployed ML projects.

```
llm-cloud-inference/
├── README.md                    # Project overview and quick start
├── LICENSE                      # MIT or Apache 2.0
├── .gitignore
├── .github/
│   └── workflows/
│       ├── build.yml            # CI: Build and push container
│       └── deploy.yml           # CD: Deploy to Cloud Run
├── docker/
│   ├── Dockerfile               # Main container definition
│   ├── Dockerfile.dev           # Local development container
│   └── startup.sh               # Container startup script
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── health.py                # Health check endpoints
│   └── middleware.py            # API key auth, rate limiting
├── scripts/
│   ├── upload_model.sh          # Upload model to GCS
│   ├── deploy.sh                # Deploy to Cloud Run
│   ├── benchmark_latency.py     # Latency comparison script
│   └── download_and_quantize.py # Model preparation
├── benchmarks/
│   ├── results/                 # Benchmark output files
│   └── report_template.md       # Benchmark report template
├── terraform/                   # Optional: IaC for GCP resources
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docs/
│   ├── ARCHITECTURE.md          # Detailed architecture decisions
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── BENCHMARKS.md            # Benchmark methodology
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
└── Makefile                     # Common commands
```

### Git Workflow

```bash
# Initialize repository
git init llm-cloud-inference
cd llm-cloud-inference
git remote add origin git@github.com:YOUR_USERNAME/llm-cloud-inference.git

# Branch strategy
main           # Production-ready code
develop        # Integration branch
feature/*      # Feature branches
```

---

## 🔧 Inference Engine Selection

Based on [Awesome-local-LLM](https://github.com/rafska/Awesome-local-LLM) research:

### Engine Comparison Matrix

| Engine | Throughput | Memory Efficiency | OpenAI Compatible | Cloud Run Ready | Best For |
|--------|------------|-------------------|-------------------|-----------------|----------|
| **vLLM** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Native | ✅ Yes | Production serving |
| **sglang** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Yes | ✅ Yes | Multi-modal, fast |
| **llama.cpp** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Via wrapper | ✅ Yes | CPU/Low memory |
| **Nano-vLLM** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Yes | Minimal footprint |
| **Ollama** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Yes | ⚠️ Tricky | Local dev |

### Recommended: vLLM (Primary) with sglang (Alternative)

**vLLM Advantages**:
- PagedAttention for optimal memory usage
- Continuous batching for high throughput
- Native OpenAI-compatible API
- Active community (PyTorch Foundation project as of May 2025)
- Well-documented Cloud Run deployment

**sglang Alternative**:
- Faster for certain workloads
- Better multi-modal support
- Good for vision-language models

### Decision Matrix by Use Case

```
If prioritizing...
├── Maximum throughput → vLLM
├── Vision + Language → sglang
├── Minimal memory → llama.cpp (GGUF)
├── Simplest setup → Ollama
└── Cutting-edge features → sglang
```

---

## 🤖 Model Selection Guide (2025)

Based on [Awesome-local-LLM](https://github.com/rafska/Awesome-local-LLM) model collections:

### Recommended Models by GPU Memory

| GPU | VRAM | Recommended Models | Quantization |
|-----|------|-------------------|--------------|
| T4 | 16GB | Phi-4-mini, Gemma-3-4B, Qwen3-4B | 4-bit |
| L4 | 24GB | Qwen3-8B, Gemma-3-12B, Llama-3.1-8B | 4-bit or 8-bit |
| A100 40GB | 40GB | Qwen3-32B, Llama-3.1-70B | 4-bit |
| A100 80GB | 80GB | Full precision for most models | FP16 |

### Model Recommendations by Task

**General Purpose (Cost-Optimized)**:
```yaml
Primary: Qwen3-8B-Instruct (Q4_K_M)
- Excellent reasoning
- Multilingual
- Fits on L4 with room for context

Alternative: Gemma-3-12B-Instruct
- Google's latest
- Strong coding capabilities
- Efficient architecture
```

**Code-Focused**:
```yaml
Primary: Qwen3-Coder-8B (Q4_K_M)
- Purpose-built for code
- Strong at agentic tasks

Alternative: Devstral-Small
- Mistral's code model
- Good at software engineering
```

**Lightweight/Fast**:
```yaml
Primary: Phi-4-mini-instruct
- Microsoft's efficient model
- Surprisingly capable
- Very fast inference
```

### Model Download & Quantization

```bash
# scripts/download_and_quantize.py
#!/usr/bin/env python3
"""Download and optionally quantize models for deployment."""

import os
from huggingface_hub import snapshot_download
from pathlib import Path

# Configuration
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"  # Or your chosen model
LOCAL_DIR = Path("./models")
QUANTIZATION = "awq"  # Options: none, awq, gptq, gguf

def download_model():
    """Download model from Hugging Face."""
    print(f"Downloading {MODEL_ID}...")
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=LOCAL_DIR / MODEL_ID.split("/")[-1],
        local_dir_use_symlinks=False,
    )
    print("Download complete!")

def get_quantized_model():
    """Get pre-quantized model if available."""
    # Many models have pre-quantized versions
    quantized_id = f"{MODEL_ID}-AWQ"  # or -GPTQ
    print(f"Downloading pre-quantized {quantized_id}...")
    snapshot_download(
        repo_id=quantized_id,
        local_dir=LOCAL_DIR / quantized_id.split("/")[-1],
        local_dir_use_symlinks=False,
    )

if __name__ == "__main__":
    download_model()
```

---

## 🔢 Quantization Methodology

### Quantization Formats Comparison

| Format | Size Reduction | Quality Loss | vLLM Support | Best For |
|--------|---------------|--------------|--------------|----------|
| FP16 | Baseline | None | ✅ | Maximum quality |
| INT8 | 50% | Minimal | ✅ | Balanced |
| AWQ 4-bit | 75% | Low | ✅ | Production |
| GPTQ 4-bit | 75% | Low | ✅ | Production |
| GGUF Q4_K_M | 75% | Low | ⚠️ via llama.cpp | CPU/Edge |

### Recommended: AWQ 4-bit Quantization

**Why AWQ**:
- Activation-aware: preserves important weights
- Excellent quality retention at 4-bit
- Native vLLM support
- Fast inference

**Pre-quantized Models** (use these to skip quantization):
- `Qwen/Qwen2.5-7B-Instruct-AWQ`
- `TheBloke/Llama-2-7B-Chat-AWQ`
- Most popular models have AWQ versions on HuggingFace

### VRAM Calculator

```python
# Approximate VRAM calculation
def estimate_vram_gb(params_billions: float, precision: str) -> float:
    """Estimate VRAM needed for a model."""
    bytes_per_param = {
        "fp32": 4,
        "fp16": 2,
        "int8": 1,
        "int4": 0.5,
    }
    base_vram = params_billions * bytes_per_param[precision]
    # Add ~20% overhead for KV cache, activations
    return base_vram * 1.2

# Examples:
# 7B model at FP16: 7 * 2 * 1.2 = 16.8 GB
# 7B model at INT4: 7 * 0.5 * 1.2 = 4.2 GB
```

---

## 🏗️ Architecture: vLLM + Cloud Run + GCS

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your Local Machine                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Your Application / Benchmark Script                      │   │
│  │  - Python with openai SDK                                 │   │
│  │  - Latency measurement instrumentation                    │   │
│  └──────────────────┬───────────────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────────────┘
                      │
                      │ HTTPS Request (OpenAI-compatible)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Google Cloud Platform (GCP)                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Cloud Run Service                       │   │
│  │  ┌──────────────────────────────────────────────────────┐ │   │
│  │  │              Container Instance                       │ │   │
│  │  │  ┌────────────────────────────────────────────────┐  │ │   │
│  │  │  │  vLLM Server                                    │  │ │   │
│  │  │  │  - OpenAI-compatible /v1/chat/completions       │  │ │   │
│  │  │  │  - /v1/completions                              │  │ │   │
│  │  │  │  - /v1/models                                   │  │ │   │
│  │  │  │  - /health (for Cloud Run probes)               │  │ │   │
│  │  │  └────────────────────────────────────────────────┘  │ │   │
│  │  │  GPU: NVIDIA L4 (24GB VRAM)                          │ │   │
│  │  │  Model: Qwen2.5-7B-Instruct-AWQ (4-bit, ~4GB)        │ │   │
│  │  └──────────────────────────────────────────────────────┘ │   │
│  │  Config: min_instances=0, max_instances=3, timeout=3600s  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      │ Downloads model (cold start)              │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Google Cloud Storage (GCS)                        │   │
│  │  Bucket: llm-cloud-inference-models                       │   │
│  │  └── qwen2.5-7b-instruct-awq/                             │   │
│  │      ├── config.json                                      │   │
│  │      ├── model.safetensors                                │   │
│  │      └── tokenizer.json                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Observability Stack (Optional but Recommended)           │   │
│  │  - Cloud Monitoring (metrics)                             │   │
│  │  - Cloud Logging (structured logs)                        │   │
│  │  - Langfuse (LLM-specific observability)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Implementation Files

### Dockerfile

```dockerfile
# docker/Dockerfile
FROM vllm/vllm-openai:v0.6.4.post1

# Install GCS access tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV MODEL_NAME="qwen2.5-7b-instruct-awq"
ENV GCS_BUCKET="llm-cloud-inference-models"
ENV PORT=8080
ENV VLLM_ATTENTION_BACKEND=FLASHINFER

# Create model directory
RUN mkdir -p /models

# Copy startup script
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

ENTRYPOINT ["/startup.sh"]
```

### Startup Script

```bash
#!/bin/bash
# docker/startup.sh
set -e

echo "=== LLM Cloud Inference Startup ==="
echo "Model: ${MODEL_NAME}"
echo "GCS Bucket: ${GCS_BUCKET}"
echo "Port: ${PORT}"

# Download model from GCS if not already present
MODEL_PATH="/models/${MODEL_NAME}"
if [ ! -d "${MODEL_PATH}" ] || [ -z "$(ls -A ${MODEL_PATH} 2>/dev/null)" ]; then
    echo "Downloading model from GCS..."
    mkdir -p "${MODEL_PATH}"
    gcloud storage cp -r "gs://${GCS_BUCKET}/${MODEL_NAME}/*" "${MODEL_PATH}/"
    echo "Model download complete!"
else
    echo "Model already cached locally."
fi

# Calculate optimal settings based on GPU
GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
echo "GPU Memory: ${GPU_MEMORY}MB"

# Start vLLM server with optimized settings
echo "Starting vLLM server..."
exec python -m vllm.entrypoints.openai.api_server \
    --model "${MODEL_PATH}" \
    --host 0.0.0.0 \
    --port ${PORT} \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --dtype auto \
    --trust-remote-code \
    --disable-log-requests \
    --served-model-name "${MODEL_NAME}"
```

### Configuration Management

```python
# src/config.py
"""Configuration management for LLM Cloud Inference."""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration."""

    # Model settings
    model_name: str = os.getenv("MODEL_NAME", "qwen2.5-7b-instruct-awq")
    gcs_bucket: str = os.getenv("GCS_BUCKET", "llm-cloud-inference-models")
    model_path: str = os.getenv("MODEL_PATH", "/models")

    # Server settings
    port: int = int(os.getenv("PORT", "8080"))
    host: str = os.getenv("HOST", "0.0.0.0")

    # vLLM settings
    gpu_memory_utilization: float = float(os.getenv("GPU_MEMORY_UTIL", "0.90"))
    max_model_len: int = int(os.getenv("MAX_MODEL_LEN", "8192"))

    # Security
    api_key: Optional[str] = os.getenv("API_KEY")
    require_auth: bool = os.getenv("REQUIRE_AUTH", "false").lower() == "true"

    @property
    def full_model_path(self) -> str:
        return f"{self.model_path}/{self.model_name}"

config = Config()
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy.sh
set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="llm-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/llm-cloud-inference:latest"

echo "=== Deploying LLM Cloud Inference ==="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Image: ${IMAGE_NAME}"

# Build and push container
echo "Building container..."
docker build -t ${IMAGE_NAME} -f docker/Dockerfile .

echo "Pushing to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --cpu 8 \
    --memory 32Gi \
    --timeout 3600 \
    --min-instances 0 \
    --max-instances 3 \
    --concurrency 10 \
    --port 8080 \
    --set-env-vars "MODEL_NAME=qwen2.5-7b-instruct-awq,GCS_BUCKET=llm-cloud-inference-models" \
    --service-account "llm-inference@${PROJECT_ID}.iam.gserviceaccount.com" \
    --allow-unauthenticated

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "=== Deployment Complete ==="
echo "Service URL: ${SERVICE_URL}"
echo "Test with: curl ${SERVICE_URL}/v1/models"
```

### Makefile

```makefile
# Makefile
.PHONY: help setup download-model build push deploy test benchmark clean

PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= us-central1
IMAGE_NAME = gcr.io/$(PROJECT_ID)/llm-cloud-inference
MODEL_NAME ?= qwen2.5-7b-instruct-awq

help:
	@echo "LLM Cloud Inference - Available commands:"
	@echo "  make setup          - Set up GCP project and enable APIs"
	@echo "  make download-model - Download and prepare model"
	@echo "  make upload-model   - Upload model to GCS"
	@echo "  make build          - Build Docker container"
	@echo "  make push           - Push to Google Container Registry"
	@echo "  make deploy         - Deploy to Cloud Run"
	@echo "  make test           - Test deployed API"
	@echo "  make benchmark      - Run latency benchmarks"
	@echo "  make logs           - View Cloud Run logs"
	@echo "  make clean          - Clean up local resources"

setup:
	@echo "Setting up GCP project..."
	gcloud services enable run.googleapis.com
	gcloud services enable containerregistry.googleapis.com
	gcloud services enable storage.googleapis.com
	gcloud services enable cloudbuild.googleapis.com
	@echo "Creating GCS bucket..."
	gsutil mb -l $(REGION) gs://llm-cloud-inference-models || true
	@echo "Creating service account..."
	gcloud iam service-accounts create llm-inference --display-name "LLM Inference Service" || true
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
		--member="serviceAccount:llm-inference@$(PROJECT_ID).iam.gserviceaccount.com" \
		--role="roles/storage.objectViewer"

download-model:
	python scripts/download_and_quantize.py

upload-model:
	@echo "Uploading model to GCS..."
	gsutil -m cp -r ./models/$(MODEL_NAME)/* gs://llm-cloud-inference-models/$(MODEL_NAME)/

build:
	docker build -t $(IMAGE_NAME):latest -f docker/Dockerfile .

push: build
	docker push $(IMAGE_NAME):latest

deploy: push
	./scripts/deploy.sh

test:
	@SERVICE_URL=$$(gcloud run services describe llm-api --region $(REGION) --format 'value(status.url)'); \
	echo "Testing $$SERVICE_URL..."; \
	curl -s "$$SERVICE_URL/v1/models" | jq .

benchmark:
	python scripts/benchmark_latency.py

logs:
	gcloud run services logs read llm-api --region $(REGION) --limit 100

clean:
	rm -rf ./models/*
	docker rmi $(IMAGE_NAME):latest || true
```

---

## 📊 Latency Benchmarking: Self-Hosted vs Commercial APIs

### Benchmark Script

```python
#!/usr/bin/env python3
# scripts/benchmark_latency.py
"""
Benchmark latency comparison: Self-hosted LLM vs Commercial APIs
Measures: TTFT, TPS, Total latency, Cost per token
"""

import asyncio
import json
import os
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from openai import OpenAI, AsyncOpenAI

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class BenchmarkConfig:
    """Benchmark configuration."""
    # Endpoints
    self_hosted_url: str = os.getenv("SELF_HOSTED_URL", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Test parameters
    num_runs: int = 10
    warmup_runs: int = 2
    max_tokens: int = 256
    temperature: float = 0.7

    # Test prompts (varying complexity)
    prompts: list = field(default_factory=lambda: [
        # Short prompt
        "What is 2+2?",
        # Medium prompt
        "Explain the concept of machine learning in 3 sentences.",
        # Long prompt
        "Write a detailed comparison of Python and JavaScript for web development, covering syntax, performance, ecosystem, and use cases.",
    ])

@dataclass
class LatencyResult:
    """Single request latency measurements."""
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    ttft_ms: float  # Time to first token
    total_ms: float  # Total request time
    tps: float  # Tokens per second
    cost_usd: float  # Estimated cost
    error: Optional[str] = None

@dataclass
class BenchmarkReport:
    """Aggregated benchmark results."""
    provider: str
    model: str
    num_requests: int
    avg_ttft_ms: float
    p50_ttft_ms: float
    p95_ttft_ms: float
    avg_total_ms: float
    p50_total_ms: float
    p95_total_ms: float
    avg_tps: float
    total_cost_usd: float
    error_rate: float

# =============================================================================
# Pricing (as of Dec 2025)
# =============================================================================

PRICING = {
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "claude-3-5-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "claude-3-5-haiku": {"input": 0.80 / 1_000_000, "output": 4.00 / 1_000_000},
    "self-hosted": {"input": 0, "output": 0},  # Cost calculated separately
}

# =============================================================================
# Benchmark Functions
# =============================================================================

async def benchmark_openai(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    config: BenchmarkConfig,
) -> LatencyResult:
    """Benchmark OpenAI API."""
    start_time = time.perf_counter()
    ttft = None
    tokens_received = 0

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            stream=True,
        )

        async for chunk in stream:
            if ttft is None:
                ttft = (time.perf_counter() - start_time) * 1000
            if chunk.choices[0].delta.content:
                tokens_received += 1

        total_time = (time.perf_counter() - start_time) * 1000

        # Estimate prompt tokens (rough: 4 chars per token)
        prompt_tokens = len(prompt) // 4

        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        cost = (prompt_tokens * pricing["input"]) + (tokens_received * pricing["output"])

        return LatencyResult(
            provider="OpenAI",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=tokens_received,
            ttft_ms=ttft or total_time,
            total_ms=total_time,
            tps=tokens_received / (total_time / 1000) if total_time > 0 else 0,
            cost_usd=cost,
        )
    except Exception as e:
        return LatencyResult(
            provider="OpenAI",
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            ttft_ms=0,
            total_ms=0,
            tps=0,
            cost_usd=0,
            error=str(e),
        )

async def benchmark_self_hosted(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    config: BenchmarkConfig,
) -> LatencyResult:
    """Benchmark self-hosted vLLM API."""
    start_time = time.perf_counter()
    ttft = None
    tokens_received = 0

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            stream=True,
        )

        async for chunk in stream:
            if ttft is None:
                ttft = (time.perf_counter() - start_time) * 1000
            if chunk.choices[0].delta.content:
                tokens_received += 1

        total_time = (time.perf_counter() - start_time) * 1000
        prompt_tokens = len(prompt) // 4

        return LatencyResult(
            provider="Self-Hosted",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=tokens_received,
            ttft_ms=ttft or total_time,
            total_ms=total_time,
            tps=tokens_received / (total_time / 1000) if total_time > 0 else 0,
            cost_usd=0,  # Calculated from Cloud Run billing
        )
    except Exception as e:
        return LatencyResult(
            provider="Self-Hosted",
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            ttft_ms=0,
            total_ms=0,
            tps=0,
            cost_usd=0,
            error=str(e),
        )

def calculate_percentile(values: list[float], percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]

def aggregate_results(results: list[LatencyResult]) -> BenchmarkReport:
    """Aggregate individual results into a report."""
    successful = [r for r in results if r.error is None]

    if not successful:
        return BenchmarkReport(
            provider=results[0].provider if results else "Unknown",
            model=results[0].model if results else "Unknown",
            num_requests=len(results),
            avg_ttft_ms=0,
            p50_ttft_ms=0,
            p95_ttft_ms=0,
            avg_total_ms=0,
            p50_total_ms=0,
            p95_total_ms=0,
            avg_tps=0,
            total_cost_usd=0,
            error_rate=1.0,
        )

    ttft_values = [r.ttft_ms for r in successful]
    total_values = [r.total_ms for r in successful]
    tps_values = [r.tps for r in successful]

    return BenchmarkReport(
        provider=successful[0].provider,
        model=successful[0].model,
        num_requests=len(results),
        avg_ttft_ms=statistics.mean(ttft_values),
        p50_ttft_ms=calculate_percentile(ttft_values, 50),
        p95_ttft_ms=calculate_percentile(ttft_values, 95),
        avg_total_ms=statistics.mean(total_values),
        p50_total_ms=calculate_percentile(total_values, 50),
        p95_total_ms=calculate_percentile(total_values, 95),
        avg_tps=statistics.mean(tps_values),
        total_cost_usd=sum(r.cost_usd for r in successful),
        error_rate=(len(results) - len(successful)) / len(results),
    )

async def run_benchmark(config: BenchmarkConfig) -> dict:
    """Run full benchmark suite."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "num_runs": config.num_runs,
            "max_tokens": config.max_tokens,
            "prompts": config.prompts,
        },
        "reports": [],
    }

    # Initialize clients
    clients = {}

    if config.openai_api_key:
        clients["openai"] = AsyncOpenAI(api_key=config.openai_api_key)

    if config.self_hosted_url:
        clients["self_hosted"] = AsyncOpenAI(
            base_url=f"{config.self_hosted_url}/v1",
            api_key="dummy",  # vLLM doesn't require auth by default
        )

    # Run benchmarks
    for prompt in config.prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt[:50]}...")
        print(f"{'='*60}")

        # OpenAI benchmarks
        if "openai" in clients:
            for model in ["gpt-4o-mini", "gpt-4o"]:
                print(f"\nBenchmarking OpenAI {model}...")
                model_results = []

                # Warmup
                for _ in range(config.warmup_runs):
                    await benchmark_openai(clients["openai"], model, prompt, config)

                # Actual runs
                for i in range(config.num_runs):
                    result = await benchmark_openai(clients["openai"], model, prompt, config)
                    model_results.append(result)
                    print(f"  Run {i+1}: TTFT={result.ttft_ms:.0f}ms, Total={result.total_ms:.0f}ms, TPS={result.tps:.1f}")

                report = aggregate_results(model_results)
                results["reports"].append({
                    "prompt_preview": prompt[:50],
                    **report.__dict__,
                })

        # Self-hosted benchmark
        if "self_hosted" in clients:
            print(f"\nBenchmarking Self-Hosted...")
            model_results = []
            model_name = os.getenv("MODEL_NAME", "qwen2.5-7b-instruct-awq")

            # Warmup
            for _ in range(config.warmup_runs):
                await benchmark_self_hosted(clients["self_hosted"], model_name, prompt, config)

            # Actual runs
            for i in range(config.num_runs):
                result = await benchmark_self_hosted(clients["self_hosted"], model_name, prompt, config)
                model_results.append(result)
                print(f"  Run {i+1}: TTFT={result.ttft_ms:.0f}ms, Total={result.total_ms:.0f}ms, TPS={result.tps:.1f}")

            report = aggregate_results(model_results)
            results["reports"].append({
                "prompt_preview": prompt[:50],
                **report.__dict__,
            })

    return results

def print_summary(results: dict):
    """Print benchmark summary."""
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)

    # Group by provider
    by_provider = {}
    for report in results["reports"]:
        provider = report["provider"]
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(report)

    for provider, reports in by_provider.items():
        print(f"\n{provider}:")
        print("-" * 40)

        avg_ttft = statistics.mean(r["avg_ttft_ms"] for r in reports)
        avg_total = statistics.mean(r["avg_total_ms"] for r in reports)
        avg_tps = statistics.mean(r["avg_tps"] for r in reports)
        total_cost = sum(r["total_cost_usd"] for r in reports)

        print(f"  Avg TTFT:     {avg_ttft:>8.1f} ms")
        print(f"  Avg Total:    {avg_total:>8.1f} ms")
        print(f"  Avg TPS:      {avg_tps:>8.1f} tokens/sec")
        print(f"  Total Cost:   ${total_cost:>7.4f}")

def save_results(results: dict, output_dir: str = "benchmarks/results"):
    """Save benchmark results to JSON."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(output_dir) / f"benchmark_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

async def main():
    """Main entry point."""
    config = BenchmarkConfig()

    if not config.self_hosted_url and not config.openai_api_key:
        print("Error: Set SELF_HOSTED_URL or OPENAI_API_KEY environment variable")
        return

    print("Starting LLM Latency Benchmark...")
    print(f"Configuration: {config.num_runs} runs, {config.max_tokens} max tokens")

    results = await run_benchmark(config)
    print_summary(results)
    save_results(results)

if __name__ == "__main__":
    asyncio.run(main())
```

### Expected Benchmark Results

Based on typical observations:

| Provider | Model | TTFT (p50) | Total (p50) | TPS | Cost/1K tokens |
|----------|-------|------------|-------------|-----|----------------|
| OpenAI | gpt-4o-mini | 200-400ms | 1-3s | 50-100 | $0.075 |
| OpenAI | gpt-4o | 300-600ms | 2-5s | 40-80 | $6.25 |
| Self-hosted (warm) | Qwen-7B | 100-300ms | 1-2s | 30-60 | ~$0.01* |
| Self-hosted (cold) | Qwen-7B | 60-180s | 60-180s | - | ~$0.01* |

*Self-hosted cost = Cloud Run compute time, roughly $1-2/hour when active

### Key Insights for Portfolio

1. **Cold start is the main trade-off**: Self-hosted is cheaper but has significant cold start
2. **Warm latency is competitive**: Once running, self-hosted can match or beat API latency
3. **Cost efficiency**: At high volumes, self-hosted is 10-100x cheaper
4. **Control**: Self-hosted offers full control over model, context, and data

---

## 📈 Observability & Monitoring

Based on [Awesome-local-LLM](https://github.com/rafska/Awesome-local-LLM) observability tools:

### Option 1: Cloud Monitoring (Included with GCP)

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Create custom dashboard
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json
```

Key metrics to track:
- Request latency (p50, p95, p99)
- Request count by status code
- GPU utilization
- Memory utilization
- Cold start frequency

### Option 2: Langfuse (LLM-Specific Observability)

From [Awesome-local-LLM](https://github.com/rafska/Awesome-local-LLM): "langfuse - open-source LLM engineering platform"

```python
# Integration with vLLM
from langfuse import Langfuse
from langfuse.openai import openai

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
)

# Automatic tracing of OpenAI-compatible calls
client = openai.OpenAI(
    base_url="https://your-cloud-run-url/v1",
    api_key="dummy",
)

# All calls are now traced in Langfuse
response = client.chat.completions.create(...)
```

Benefits:
- Token usage tracking
- Latency histograms
- Cost tracking
- Prompt versioning
- Evaluation pipelines

### Option 3: OpenLLMetry (OpenTelemetry-based)

From [Awesome-local-LLM](https://github.com/rafska/Awesome-local-LLM): "openllmetry - observability for LLM applications based on OpenTelemetry"

```python
from opentelemetry import trace
from traceloop.sdk import Traceloop

Traceloop.init(app_name="llm-cloud-inference")
```

---

## 💰 Cost Analysis (Updated)

### Cloud Run GPU Pricing (Dec 2025)

| GPU | vCPU | Memory | Price/hour | Monthly (24/7) |
|-----|------|--------|------------|----------------|
| T4 | 4 | 16GB | ~$0.40 | ~$288 |
| L4 | 8 | 32GB | ~$0.90 | ~$648 |
| A100 40GB | 12 | 85GB | ~$2.50 | ~$1,800 |

### Cost Optimization Strategies

1. **min_instances=0**: Pay nothing when idle
2. **Use quantized models**: Fit larger models on smaller GPUs
3. **Right-size GPU**: T4 for <7B, L4 for 7B-13B, A100 for larger
4. **Set aggressive timeout**: Prevent runaway costs
5. **Implement caching**: Reduce redundant inference

### Break-even Analysis

```
OpenAI GPT-4o-mini: $0.15/1M input + $0.60/1M output ≈ $0.075/1K tokens

Self-hosted L4 GPU: $0.90/hour
At 50 tokens/second = 180K tokens/hour
Cost per 1K tokens = $0.90 / 180 = $0.005

Break-even: Self-hosted is cheaper at >~13 hours/month usage
```

---

## 📋 Implementation Milestones (Updated)

### Phase 1: Setup (Day 1-2) ✅ CURRENT
- [x] Research architecture options
- [x] Document architecture decisions
- [ ] Create GitHub repository `llm-cloud-inference`
- [ ] Set up GCP project and enable APIs
- [ ] Configure billing alerts ($50 limit)

### Phase 2: Model Preparation (Day 3-4)
- [ ] Download Qwen2.5-7B-Instruct-AWQ
- [ ] Create GCS bucket
- [ ] Upload model to GCS
- [ ] Verify model accessibility

### Phase 3: Container Development (Day 5-7)
- [ ] Create Dockerfile
- [ ] Create startup script
- [ ] Test container locally with Docker + GPU
- [ ] Push to Google Container Registry

### Phase 4: Deployment (Day 8-10)
- [ ] Deploy to Cloud Run with GPU
- [ ] Configure environment variables
- [ ] Test API endpoints
- [ ] Measure cold start time

### Phase 5: Benchmarking (Day 11-13)
- [ ] Set up benchmark script
- [ ] Run latency comparison vs OpenAI
- [ ] Generate benchmark report
- [ ] Document findings

### Phase 6: Optimization & Documentation (Day 14)
- [ ] Optimize based on benchmarks
- [ ] Set up observability
- [ ] Complete documentation
- [ ] Prepare portfolio presentation

---

## 🔒 Security Best Practices

### API Authentication

```python
# src/middleware.py
from fastapi import Request, HTTPException
from functools import wraps

async def verify_api_key(request: Request):
    """Verify API key from header."""
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    expected_key = os.getenv("API_KEY")

    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

### Cloud Run Security

```bash
# Deploy with authentication required
gcloud run deploy llm-api \
    --no-allow-unauthenticated \
    --service-account llm-inference@${PROJECT_ID}.iam.gserviceaccount.com

# Generate identity token for access
gcloud auth print-identity-token
```

### Secrets Management

```bash
# Store API keys in Secret Manager
gcloud secrets create llm-api-key --replication-policy="automatic"
echo -n "your-secret-key" | gcloud secrets versions add llm-api-key --data-file=-

# Reference in Cloud Run
gcloud run deploy llm-api \
    --set-secrets="API_KEY=llm-api-key:latest"
```

---

## 🎯 Career Value & Portfolio

### Skills Demonstrated

| Category | Skills |
|----------|--------|
| **Cloud Infrastructure** | GCP, Cloud Run, GCS, Container Registry |
| **ML Engineering** | LLM deployment, vLLM, model quantization |
| **DevOps** | Docker, CI/CD, IaC concepts |
| **Performance Engineering** | Latency benchmarking, optimization |
| **API Design** | OpenAI-compatible REST APIs |
| **Cost Optimization** | Serverless architecture, resource right-sizing |

### Interview Talking Points

1. **"Deployed production LLM infrastructure achieving 10-100x cost reduction vs commercial APIs"**
   - Quantified cost comparison with benchmark data

2. **"Implemented OpenAI-compatible API enabling zero-code migration for existing applications"**
   - Drop-in replacement architecture

3. **"Optimized cold start latency from 5 minutes to <3 minutes through model quantization"**
   - AWQ 4-bit quantization, model selection

4. **"Built comprehensive latency benchmarking suite comparing self-hosted vs commercial APIs"**
   - TTFT, TPS, total latency metrics

5. **"Designed serverless GPU architecture with scale-to-zero for optimal cost efficiency"**
   - Cloud Run min_instances=0 pattern

### GitHub README Structure

```markdown
# LLM Cloud Inference

Deploy your own OpenAI-compatible LLM API on Google Cloud Run with GPU support.

## Features
- 🚀 OpenAI-compatible API endpoints
- 💰 Scale-to-zero for cost optimization
- 📊 Comprehensive latency benchmarking
- 🔒 Optional authentication
- 📈 Built-in observability

## Quick Start
... (deployment commands)

## Benchmark Results
| Provider | TTFT (p50) | Cost/1K tokens |
|----------|------------|----------------|
| OpenAI gpt-4o-mini | 300ms | $0.075 |
| Self-hosted Qwen-7B | 200ms | $0.005 |

## Architecture
... (diagram)
```

---

## 🔗 Resources and References

### From Awesome-local-LLM
- [vLLM](https://github.com/vllm-project/vllm) - High-throughput inference engine
- [sglang](https://github.com/sgl-project/sglang) - Fast serving framework
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - CPU/edge inference
- [Langfuse](https://github.com/langfuse/langfuse) - LLM observability
- [OpenLLMetry](https://github.com/traceloop/openllmetry) - OpenTelemetry for LLMs

### Official Documentation
- [vLLM Documentation](https://docs.vllm.ai/)
- [Cloud Run GPU Documentation](https://cloud.google.com/run/docs/configuring/services/gpu)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)

### Communities
- [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA) - Local LLM discussions
- [r/selfhosted](https://reddit.com/r/selfhosted) - Self-hosting community

---

*Document Version: 2.0*
*Last Updated: December 2025*
*Source: Enhanced with [Awesome-local-LLM](https://github.com/rafska/Awesome-local-LLM) research*
