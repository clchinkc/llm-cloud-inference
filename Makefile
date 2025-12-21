.PHONY: help setup download-model upload-model build build-baked push push-baked deploy deploy-baked test chat example benchmark logs clean

PROJECT_ID ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-southeast1
IMAGE_NAME = gcr.io/$(PROJECT_ID)/llm-cloud-inference
MODEL_NAME ?= qwen3-8b-awq
GCS_BUCKET ?= $(PROJECT_ID)-models

help:
	@echo "LLM Cloud Inference"
	@echo ""
	@echo "Standard (GCS download on startup, cold start ~4-5 minutes):"
	@echo "  make build          - Build container"
	@echo "  make deploy         - Deploy to Cloud Run"
	@echo ""
	@echo "Baked (model pre-baked in image, cold start ~4-5 minutes):"
	@echo "  make build-baked    - Build container with model baked in"
	@echo "  make deploy-baked   - Deploy baked container"
	@echo ""
	@echo "Other commands:"
	@echo "  make setup          - Set up GCP project"
	@echo "  make download-model - Download model"
	@echo "  make test           - Test API"
	@echo "  make chat           - Interactive CLI chatbot"
	@echo "  make example        - Run API examples (for scripts)"
	@echo "  make benchmark      - Run latency benchmarks"
	@echo "  make logs           - View logs"

setup:
	gcloud services enable run.googleapis.com containerregistry.googleapis.com storage.googleapis.com
	gsutil mb -l $(REGION) gs://$(GCS_BUCKET) || true
	gcloud iam service-accounts create llm-inference --display-name "LLM Inference" || true
	gcloud projects add-iam-policy-binding $(PROJECT_ID) \
		--member="serviceAccount:llm-inference@$(PROJECT_ID).iam.gserviceaccount.com" \
		--role="roles/storage.objectViewer"

download-model:
	MODEL_ID="Qwen/Qwen3-8B-AWQ" python3 scripts/download_and_quantize.py

upload-model:
	MODEL_NAME=$(MODEL_NAME) GCS_BUCKET=$(GCS_BUCKET) ./scripts/upload_model.sh

build:
	docker build -t $(IMAGE_NAME):latest -f docker/Dockerfile docker/

build-baked:
	@echo "Building baked image (model included, ~5GB)..."
	@if [ ! -d "models/$(MODEL_NAME)" ]; then echo "Error: Run 'make download-model' first"; exit 1; fi
	cp -r models/$(MODEL_NAME) docker/models/
	docker build -t $(IMAGE_NAME):baked -f docker/Dockerfile.baked docker/
	rm -rf docker/models/

push: build
	docker push $(IMAGE_NAME):latest

push-baked: build-baked
	docker push $(IMAGE_NAME):baked

deploy:
	GCP_PROJECT_ID=$(PROJECT_ID) GCP_REGION=$(REGION) MODEL_NAME=$(MODEL_NAME) GCS_BUCKET=$(GCS_BUCKET) ./scripts/deploy.sh

deploy-baked: push-baked
	@echo "Deploying baked image..."
	gcloud run deploy llm-api \
		--image $(IMAGE_NAME):baked \
		--platform managed \
		--region $(REGION) \
		--gpu 1 \
		--gpu-type nvidia-l4 \
		--cpu 8 \
		--memory 32Gi \
		--timeout 3600 \
		--min-instances 0 \
		--max-instances 1 \
		--port 8080 \
		--cpu-boost \
		--no-cpu-throttling \
		--set-env-vars "MODEL_NAME=$(MODEL_NAME)" \
		--service-account "llm-inference@$(PROJECT_ID).iam.gserviceaccount.com" \
		--startup-probe="tcpSocket.port=8080,initialDelaySeconds=240,timeoutSeconds=20,periodSeconds=30,failureThreshold=60" \
		--allow-unauthenticated

test:
	@URL=$$(gcloud run services describe llm-api --region $(REGION) --format 'value(status.url)'); \
	curl -s "$$URL/v1/models" | python3 -m json.tool

chat:
	@URL=$$(gcloud run services describe llm-api --region $(REGION) --format 'value(status.url)'); \
	SELF_HOSTED_URL=$$URL MODEL_NAME=$(MODEL_NAME) python3 scripts/chat.py

example:
	@URL=$$(gcloud run services describe llm-api --region $(REGION) --format 'value(status.url)'); \
	SELF_HOSTED_URL=$$URL MODEL_NAME=$(MODEL_NAME) python3 scripts/example_usage.py

benchmark:
	@URL=$$(gcloud run services describe llm-api --region $(REGION) --format 'value(status.url)'); \
	SELF_HOSTED_URL=$$URL MODEL_NAME=$(MODEL_NAME) python3 scripts/benchmark_latency.py

logs:
	gcloud run services logs read llm-api --region $(REGION) --limit 50

clean:
	rm -rf ./models/*
	docker rmi $(IMAGE_NAME):latest 2>/dev/null || true
