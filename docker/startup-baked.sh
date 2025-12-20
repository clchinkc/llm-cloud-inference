#!/bin/bash

# Redirect all output to stdout/stderr for Cloud Run logging
exec 1>&1
exec 2>&1

echo "=== LLM Cloud Inference Startup (Baked Model) ==="
echo "Model: ${MODEL_NAME}"
echo "Model is pre-baked - no download needed!"

MODEL_PATH="/models/${MODEL_NAME}"

echo "Verifying model files..."
ls -lh "${MODEL_PATH}" | head -5

echo "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "Starting vLLM..."

exec python3 -m vllm.entrypoints.openai.api_server \
    --model "${MODEL_PATH}" \
    --host 0.0.0.0 \
    --port ${PORT} \
    --gpu-memory-utilization 0.80 \
    --max-model-len 8192 \
    --max-num-seqs 64 \
    --dtype auto \
    --trust-remote-code \
    --disable-log-requests \
    --served-model-name "${MODEL_NAME}"
