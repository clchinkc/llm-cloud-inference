#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
REGION="${GCP_REGION:-asia-southeast1}"
SERVICE_NAME="llm-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/llm-cloud-inference:latest"
MODEL_NAME="${MODEL_NAME:-qwen3-8b-awq}"
GCS_BUCKET="${GCS_BUCKET:-${PROJECT_ID}-models}"

echo "=== Deploying LLM Cloud Inference ==="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Model: ${MODEL_NAME}"

docker build -t ${IMAGE_NAME} -f docker/Dockerfile docker/
docker push ${IMAGE_NAME}

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
    --max-instances 1 \
    --concurrency 10 \
    --port 8080 \
    --cpu-boost \
    --no-cpu-throttling \
    --set-env-vars "MODEL_NAME=${MODEL_NAME},GCS_BUCKET=${GCS_BUCKET}" \
    --service-account "llm-inference@${PROJECT_ID}.iam.gserviceaccount.com" \
    --startup-probe="tcpSocket.port=8080,initialDelaySeconds=240,timeoutSeconds=20,periodSeconds=30,failureThreshold=60" \
    --allow-unauthenticated

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "=== Deployed ==="
echo "URL: ${SERVICE_URL}"
