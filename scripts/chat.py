#!/usr/bin/env python3
"""
Simple CLI chatbot for interacting with the self-hosted LLM.
Demonstrates Google Cloud authentication with OpenAI SDK.
Usage: python scripts/chat.py
"""

import os
import subprocess
import sys

import httpx
from openai import OpenAI


def get_service_url():
    """Automatically retrieve the Cloud Run service URL if not set."""
    try:
        region = os.getenv("GCP_REGION", "asia-southeast1")
        result = subprocess.run(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                "llm-api",
                "--region",
                region,
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


def get_identity_token():
    """Get Google Cloud identity token for authentication."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


class AuthenticatedOpenAI(OpenAI):
    """Custom OpenAI client that uses Bearer token authentication."""

    def __init__(self, base_url: str, bearer_token: str, **kwargs):
        # Create custom httpx client with Bearer token in event hooks
        def add_bearer_token(request):
            request.headers["Authorization"] = f"Bearer {bearer_token}"

        # Create httpx client with event hook
        httpx_client = httpx.Client(event_hooks={"request": [add_bearer_token]})

        # Initialize with custom httpx client
        super().__init__(
            base_url=base_url,
            api_key="dummy",
            http_client=httpx_client,
            **kwargs
        )


def main():
    api_url = os.getenv("SELF_HOSTED_URL", "") or os.getenv("LLM_API_URL", "")
    model_name = os.getenv("MODEL_NAME", "qwen3-8b-awq")

    if not api_url:
        print("Attempting to retrieve service URL from Cloud Run...")
        api_url = get_service_url()
        if not api_url:
            print("Error: Could not determine API URL.")
            print("\nPlease set the environment variable:")
            print("  export SELF_HOSTED_URL=https://llm-api-xxx.run.app")
            print("  # or")
            print("  export LLM_API_URL=https://llm-api-xxx.run.app")
            print("\nTo find your service URL, run:")
            cmd = (
                "gcloud run services describe llm-api --region "
                "asia-southeast1 --format 'value(status.url)'"
            )
            print(f"  {cmd}")
            sys.exit(1)

    # Get identity token for authentication
    print("Getting authentication token...")
    token = get_identity_token()
    if not token:
        print("Error: Could not get identity token.")
        print("Make sure you are authenticated: gcloud auth login")
        sys.exit(1)

    client = AuthenticatedOpenAI(base_url=f"{api_url}/v1", bearer_token=token)
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    print(f"Connected to {api_url}")
    print(f"Model: {model_name}")
    print("Type 'quit' to exit, 'clear' to reset conversation.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "clear":
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            print("Conversation cleared.\n")
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            print("Assistant: ", end="", flush=True)
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=1024,
                stream=True,
            )
            response_text = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        print(content, end="", flush=True)
                        response_text += content
            print("\n")
            messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            print(f"\nError: {e}\n")
            messages.pop()  # Remove failed user message


if __name__ == "__main__":
    main()
