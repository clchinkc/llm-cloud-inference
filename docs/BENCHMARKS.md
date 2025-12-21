# Benchmarks

## Metrics

- **TTFT (p50)**: Time to first token - 50th percentile latency
- **TPS**: Tokens per second - throughput during generation
- **Cost**: Computed based on Cloud Run L4 GPU pricing ($0.90/hour when active)

## Running Benchmarks

```bash
make benchmark
```

Or manually:
```bash
export SELF_HOSTED_URL="https://your-cloud-run-url"
export OPENAI_API_KEY="sk-..."  # optional, for comparing with OpenAI
python3 scripts/benchmark_latency.py
```

Results are saved to `benchmarks/results/benchmark_TIMESTAMP.json`.

## Performance Results

### Qwen3-8B-AWQ on L4 GPU (vLLM v0.8.4)

**Warm Instance Performance** (model already loaded in GPU memory):

| Provider | TTFT (p50) | Cost/1K tokens |
|----------|------------|------------------|
| Self-hosted (warm) | ~80ms | ~$0.005 |
| GPT-5 Nano | ~300ms | $0.0002-0.0004 |

**Tradeoff**:
- **GPT-5 Nano**: Cheapest (~17x less), slower (300ms)
- **Self-hosted**: Faster (80ms), ~$0.005/1K tokens, full data control

### Cold Start Performance

| Deployment Type | Cold Start | Cost |
|-----------------|-----------|------|
| Standard (GCS download) | ~4-5 minutes | $0 idle + $0.90/hr when active |
| Baked (model in image) | ~4-5 minutes | Same as standard |
| Always-warm (min_instances=1) | 0 seconds | ~$650/month 24/7 |

**Note**: Cold start time is dominated by model loading into GPU memory, not model download or container startup. Both standard and baked deployments have similar cold start times.

## Cost Analysis

### Monthly Costs (L4 GPU at $0.90/hour)

**Scale-to-Zero (Recommended)**:
- Idle: $0/month
- Active 10 hours: ~$9/month
- Active 100 hours: ~$90/month
- Active 1000 hours: ~$900/month

**Always-Warm** (min_instances=1):
- Cost: ~$648/month (24/7)
- Benefit: Zero cold start latency

### When to Use Each

**Use GPT-5 Nano if:**
- Cost is priority (~17x cheaper)
- 300ms latency acceptable
- Okay sharing data with OpenAI

**Use Self-Hosted if:**
- Latency critical (80ms required)
- Data privacy required
- High-volume inference (>100M tokens/month)

## Interpretation Guide

### TTFT (Time to First Token)
- Measures latency from request submission to receiving first response token
- Lower is better for interactive user experience
- Self-hosted ~80ms vs GPT-5 Nano ~300ms

### TPS (Tokens Per Second)
- Measures generation speed during streaming
- Self-hosted ~43 tokens/s with Qwen3-8B-AWQ
- Affected by: model size, quantization, GPU, batch size

### Factors Affecting Performance

**Improve latency**:
- Warm instance (vs cold start): ~4-5 minute improvement
- Smaller batch size: Lower TTFT but lower overall throughput
- GPU upgrade: Switch to A100 for larger models

**Improve throughput**:
- Larger batch size: More concurrent requests
- GPU memory increase: More sequences in pipeline
- Reduce max_model_len: Free up memory for batching

## Tips for Benchmarking

1. **Warm up first**: Run 2-3 requests before benchmarking to avoid cold start
2. **Use multiple prompts**: Test varies query lengths (short, medium, long)
3. **Measure in production**: Actual network latency differs from local
4. **Compare fairly**: Same max_tokens, temperature, and sampling settings
5. **Repeat runs**: Take median of 10+ runs to reduce variance

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and components
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [V1_ENGINE_ANALYSIS.md](V1_ENGINE_ANALYSIS.md) - Why we chose vLLM v0.8.4
