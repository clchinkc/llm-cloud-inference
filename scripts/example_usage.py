#!/usr/bin/env python3
"""
Example usage of the self-hosted LLM API.
Demonstrates OpenAI SDK compatibility.
"""

import os
import subprocess

from openai import OpenAI

# Configuration
API_URL = os.getenv("SELF_HOSTED_URL", "") or os.getenv("LLM_API_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-8b-awq")


def get_service_url():
    """Automatically retrieve the Cloud Run service URL if not set."""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                "llm-api",
                "--region",
                "asia-southeast1",
                "--format",
                "value(status.url)",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def main():
    api_url = API_URL

    if not api_url:
        # Try to auto-detect the service URL
        msg = (
            "No API URL found in SELF_HOSTED_URL or LLM_API_URL "
            "environment variables."
        )
        print(msg)
        print("Attempting to retrieve service URL from Cloud Run...")
        api_url = get_service_url()

        if api_url:
            print(f"Found service URL: {api_url}\n")
        else:
            print("\nError: Could not determine API URL.")
            print("\nPlease set the environment variable in one of these ways:")
            print("  Option 1: export SELF_HOSTED_URL=https://llm-api-xxx.run.app")
            print("  Option 2: export LLM_API_URL=https://llm-api-xxx.run.app")
            print("\nTo find your service URL, run:")
            cmd = (
                "gcloud run services describe llm-api --region "
                "asia-southeast1 --format 'value(status.url)'"
            )
            print(f"  {cmd}")
            print("\nOr if deployed in a different region:")
            print("  gcloud run services list --filter='name:llm-api'")
            return

    # Initialize client (OpenAI SDK compatible)
    client = OpenAI(
        base_url=f"{api_url}/v1",
        api_key="dummy",  # Not required for this deployment
    )

    # List available models
    print("=== Available Models ===")
    models = client.models.list()
    for model in models.data:
        print(f"  - {model.id}")

    # Simple chat completion
    print("\n=== Chat Completion ===")
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "What is 2+2? Answer briefly."}],
        max_tokens=50,
    )
    print(f"Response: {response.choices[0].message.content}")
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    print(f"Tokens: {prompt_tokens} in, {completion_tokens} out")

    # Streaming example
    print("\n=== Streaming Chat ===")
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "Write a haiku about coding."}],
        max_tokens=100,
        stream=True,
    )
    print("Response: ", end="")
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

    # Multi-turn conversation
    print("\n=== Multi-turn Conversation ===")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ]
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=100,
    )
    print("User: What is Python?")
    print(f"Assistant: {response.choices[0].message.content}")

    # Continue conversation
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    messages.append({"role": "user", "content": "What about JavaScript?"})
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=100,
    )
    print("\nUser: What about JavaScript?")
    print(f"Assistant: {response.choices[0].message.content}")


if __name__ == "__main__":
    main()
