FROM vllm/vllm-openai:v0.8.4

# Install google-cloud-storage for GCS access
# Upgrade transformers to support Qwen3 model (requires >= 4.51.0)
RUN pip install --no-cache-dir google-cloud-storage && \
    pip install --no-cache-dir --upgrade transformers>=4.51.0

ENV MODEL_NAME="qwen3-8b-awq"
ENV GCS_BUCKET="llm-inference-models"
ENV PORT=8080
ENV PYTHONUNBUFFERED=1


RUN mkdir -p /models

COPY docker/download_model.py /download_model.py
COPY docker/startup.sh /startup.sh
RUN chmod +x /startup.sh

EXPOSE ${PORT}
ENTRYPOINT ["/bin/bash", "-ex", "/startup.sh"]
