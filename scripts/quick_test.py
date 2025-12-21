#!/usr/bin/env python3
"""
Quick test of the authenticated LLM API.
Handles cold starts gracefully.
"""

import subprocess
import time

import httpx


def get_identity_token() -> str:
    """Get Google Cloud identity token."""
    result = subprocess.run(
        ["gcloud", "auth", "print-identity-token"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    raise RuntimeError(f"Failed to get identity token: {result.stderr}")


def get_service_url() -> str:
    """Get the Cloud Run service URL."""
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
    raise RuntimeError(f"Failed to get service URL: {result.stderr}")


def test_api_with_timeout(token: str, url: str, max_attempts: int = 12):
    """Test API endpoint with retry for cold starts (up to 2 minutes)."""
    endpoint = f"{url}/v1/models"
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Testing: {endpoint}")
    print("(First request may take 4-5 minutes due to cold start and model download)")
    print()

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt}/{max_attempts}...", end=" ", flush=True)
            response = httpx.get(endpoint, headers=headers, timeout=30)

            if response.status_code == 200:
                print("✓ SUCCESS")
                print(f"\nResponse: {response.text[:200]}")
                return True
            else:
                print(f"✗ HTTP {response.status_code}")
                if attempt < max_attempts:
                    print("  Waiting 10 seconds before retry...")
                    time.sleep(10)
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}")
            if attempt < max_attempts:
                print("  Waiting 10 seconds before retry...")
                time.sleep(10)

    print(f"\n✗ Failed after {max_attempts} attempts")
    return False


def main():
    print("=== LLM API Authentication Test ===\n")

    print("Getting service URL...")
    url = get_service_url()
    print(f"Service URL: {url}\n")

    print("Getting identity token...")
    token = get_identity_token()
    print("Token obtained\n")

    if test_api_with_timeout(token, url):
        print("\n✓ API is accessible and authenticated!")
    else:
        print("\n✗ API is not responding. Check logs:")
        print("  gcloud run services logs read llm-api")
        print("    --region asia-southeast1 --limit 50")


if __name__ == "__main__":
    main()
