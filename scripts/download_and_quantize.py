#!/usr/bin/env python3
"""Download models from Hugging Face."""

import os
from huggingface_hub import snapshot_download
from pathlib import Path

MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen3-8B-AWQ")
LOCAL_DIR = Path(os.getenv("MODEL_DIR", "./models"))


def main():
    model_name = MODEL_ID.split("/")[-1].lower()
    target_dir = LOCAL_DIR / model_name

    print(f"Downloading {MODEL_ID} to {target_dir}...")
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=target_dir,
        local_dir_use_symlinks=False,
    )
    print(f"Done. Model saved to: {target_dir}")


if __name__ == "__main__":
    main()
