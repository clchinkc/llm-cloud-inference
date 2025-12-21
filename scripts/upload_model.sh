#!/bin/bash
set -e

MODEL_NAME="${MODEL_NAME:-qwen3-8b-awq}"
GCS_BUCKET="${GCS_BUCKET:-llm-inference-models}"
LOCAL_PATH="${LOCAL_PATH:-./models/${MODEL_NAME}}"

echo "Uploading ${MODEL_NAME} to gs://${GCS_BUCKET}/${MODEL_NAME}/"

if [ ! -d "${LOCAL_PATH}" ]; then
    echo "Error: ${LOCAL_PATH} not found. Run 'make download-model' first."
    exit 1
fi

gsutil -m cp -r "${LOCAL_PATH}/*" "gs://${GCS_BUCKET}/${MODEL_NAME}/"
echo "Done."
