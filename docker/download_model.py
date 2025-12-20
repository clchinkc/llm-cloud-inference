#!/usr/bin/env python3
"""Download model from GCS using Application Default Credentials."""

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from google.cloud import storage


def download_blob(blob, dest_path: Path):
    """Download a single blob."""
    blob.download_to_filename(str(dest_path))
    print(f"  Downloaded: {blob.name}")


def download_model(bucket_name: str, model_name: str, dest_dir: str):
    """Download model files from GCS."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    prefix = f"{model_name}/"
    blobs = list(bucket.list_blobs(prefix=prefix))

    if not blobs:
        print(f"No files found in gs://{bucket_name}/{prefix}")
        sys.exit(1)

    print(f"Found {len(blobs)} files to download")

    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for blob in blobs:
            rel_path = blob.name[len(prefix):]
            if not rel_path:
                continue
            file_dest = dest_path / rel_path
            file_dest.parent.mkdir(parents=True, exist_ok=True)
            futures.append(executor.submit(download_blob, blob, file_dest))

        for future in futures:
            future.result()

    print(f"Download complete: {len(blobs)} files")


if __name__ == "__main__":
    bucket = os.environ.get("GCS_BUCKET", "")
    model = os.environ.get("MODEL_NAME", "")
    dest = f"/models/{model}"

    if not bucket or not model:
        print("GCS_BUCKET and MODEL_NAME environment variables required")
        sys.exit(1)

    print(f"Downloading gs://{bucket}/{model}/ to {dest}")
    download_model(bucket, model, dest)
