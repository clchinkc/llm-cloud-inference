#!/bin/bash

# Redirect all output to stdout/stderr for Cloud Run logging
exec 1>&1
exec 2>&1

echo "=== LLM Cloud Inference Startup ==="
echo "Model: ${MODEL_NAME}"
echo "Bucket: ${GCS_BUCKET}"
echo "Python version: $(python3 --version)"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"

MODEL_PATH="/models/${MODEL_NAME}"
echo "Model path: ${MODEL_PATH}"

if [ ! -d "${MODEL_PATH}" ] || [ -z "$(ls -A ${MODEL_PATH} 2>/dev/null)" ]; then
    echo "Downloading model from GCS..."
    python3 /download_model.py || { echo "Model download failed with exit code $?"; exit 1; }
    echo "Model download completed"
else
    echo "Model already exists at ${MODEL_PATH}"
fi

echo "Verifying model files..."
ls -lh "${MODEL_PATH}" | head -10

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
