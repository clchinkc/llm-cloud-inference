# Architecture

OpenAI-compatible LLM API on Google Cloud Run with GPU.

```
Local Machine                    Google Cloud Platform
+-------------+                  +---------------------------+
| Application | --HTTPS--->     | Cloud Run (asia-southeast1)|
| OpenAI SDK  |                  | +---------------------+   |
+-------------+                  | | vLLM Server         |   |
                                 | | /v1/chat/completions|   |
                                 | +---------------------+   |
                                 |    GPU: NVIDIA L4         |
                                 |           |               |
                                 |           v               |
                                 | +---------------------+   |
                                 | | GCS: Model weights  |   |
                                 | +---------------------+   |
                                 +---------------------------+
```

## Components

**vLLM Server (v0.8.4)**
- High-throughput inference with PagedAttention
- Native OpenAI-compatible API
- Continuous batching with optimized concurrency
- Proven stable on Cloud Run (V0 engine)

**Cloud Run**
- Serverless with GPU support (NVIDIA L4)
- Scale-to-zero (min_instances=0)
- Automatic HTTPS

**Model Storage**
- GCS bucket for model weights
- Standard: Download on first startup (~4-5 minutes cold start)
- Baked: Model pre-baked in Docker image (marginal improvement)

## Design Decisions

### Why vLLM v0.8.4?

- **V0 Single-Process Engine**: Proven stable on Cloud Run containers
- **Not v0.9.0+**: V1 multiprocess engine fails silently in containerized environments
- **Native OpenAI API**: Full compatibility with OpenAI SDK
- **Proven in Production**: Used reliably with Qwen3 models
- **Clear Error Logging**: All errors visible in Cloud Run logs (no subprocess hiding)

See [V1_ENGINE_ANALYSIS.md](V1_ENGINE_ANALYSIS.md) for detailed comparison.

### Why These Other Choices?

- **Cloud Run**: Serverless with GPU, scale-to-zero, minimal DevOps
- **AWQ 4-bit Quantization**: 75% memory reduction with minimal quality loss
- **Qwen3-8B-AWQ**: Advanced reasoning, thinking mode, multilingual, fits on L4
- **GCS for Model Storage**: Cost-effective (~$0.02/GB/month) model management
- **L4 GPU**: Optimal price-performance for 8B models (~$0.90/hour)
