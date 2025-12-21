#!/usr/bin/env python3
"""
Benchmark latency comparison: Self-hosted LLM vs Commercial APIs
Measures: TTFT, TPS, Total latency, Cost per token
"""

import asyncio
import json
import os
import statistics
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI


def _get_service_url():
    """Automatically retrieve the Cloud Run service URL if not set."""
    try:
        region = os.getenv("GCP_REGION", "asia-east2")
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


@dataclass
class BenchmarkConfig:
    """Benchmark configuration."""

    self_hosted_url: str = (
        os.getenv("SELF_HOSTED_URL", "")
        or os.getenv("LLM_API_URL", "")
        or _get_service_url()
        or ""
    )
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    num_runs: int = 10
    warmup_runs: int = 2
    max_tokens: int = 256
    temperature: float = 0.7

    prompts: list = field(
        default_factory=lambda: [
            "What is 2+2?",
            "Explain the concept of machine learning in 3 sentences.",
            "Write a comparison of Python and JavaScript for web development.",
        ]
    )


@dataclass
class LatencyResult:
    """Single request latency measurements."""

    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    ttft_ms: float
    total_ms: float
    tps: float
    cost_usd: float
    error: Optional[str] = None


PRICING = {
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "self-hosted": {"input": 0, "output": 0},
}


async def benchmark_openai(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    config: BenchmarkConfig,
) -> LatencyResult:
    """Benchmark OpenAI API."""
    start_time = time.perf_counter()
    ttft = None
    tokens_received = 0

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            stream=True,
        )

        async for chunk in stream:
            if ttft is None:
                ttft = (time.perf_counter() - start_time) * 1000
            if chunk.choices[0].delta.content:
                tokens_received += 1

        total_time = (time.perf_counter() - start_time) * 1000
        prompt_tokens = len(prompt) // 4

        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
        cost = (prompt_tokens * pricing["input"]) + (
            tokens_received * pricing["output"]
        )

        return LatencyResult(
            provider="OpenAI",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=tokens_received,
            ttft_ms=ttft or total_time,
            total_ms=total_time,
            tps=tokens_received / (total_time / 1000) if total_time > 0 else 0,
            cost_usd=cost,
        )
    except Exception as e:
        return LatencyResult(
            provider="OpenAI",
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            ttft_ms=0,
            total_ms=0,
            tps=0,
            cost_usd=0,
            error=str(e),
        )


async def benchmark_self_hosted(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    config: BenchmarkConfig,
) -> LatencyResult:
    """Benchmark self-hosted vLLM API."""
    start_time = time.perf_counter()
    ttft = None
    tokens_received = 0

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            stream=True,
        )

        async for chunk in stream:
            if ttft is None:
                ttft = (time.perf_counter() - start_time) * 1000
            if chunk.choices[0].delta.content:
                tokens_received += 1

        total_time = (time.perf_counter() - start_time) * 1000
        prompt_tokens = len(prompt) // 4

        return LatencyResult(
            provider="Self-Hosted",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=tokens_received,
            ttft_ms=ttft or total_time,
            total_ms=total_time,
            tps=tokens_received / (total_time / 1000) if total_time > 0 else 0,
            cost_usd=0,
        )
    except Exception as e:
        return LatencyResult(
            provider="Self-Hosted",
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            ttft_ms=0,
            total_ms=0,
            tps=0,
            cost_usd=0,
            error=str(e),
        )


def calculate_percentile(values: list[float], percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


def aggregate_results(results: list[LatencyResult]) -> dict:
    """Aggregate individual results into a report."""
    successful = [r for r in results if r.error is None]

    if not successful:
        return {
            "provider": results[0].provider if results else "Unknown",
            "model": results[0].model if results else "Unknown",
            "num_requests": len(results),
            "error_rate": 1.0,
        }

    ttft_values = [r.ttft_ms for r in successful]
    total_values = [r.total_ms for r in successful]
    tps_values = [r.tps for r in successful]

    return {
        "provider": successful[0].provider,
        "model": successful[0].model,
        "num_requests": len(results),
        "avg_ttft_ms": statistics.mean(ttft_values),
        "p50_ttft_ms": calculate_percentile(ttft_values, 50),
        "p95_ttft_ms": calculate_percentile(ttft_values, 95),
        "avg_total_ms": statistics.mean(total_values),
        "p50_total_ms": calculate_percentile(total_values, 50),
        "p95_total_ms": calculate_percentile(total_values, 95),
        "avg_tps": statistics.mean(tps_values),
        "total_cost_usd": sum(r.cost_usd for r in successful),
        "error_rate": (len(results) - len(successful)) / len(results),
    }


async def run_benchmark(config: BenchmarkConfig) -> dict:
    """Run full benchmark suite."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "num_runs": config.num_runs,
            "max_tokens": config.max_tokens,
            "prompts": config.prompts,
        },
        "reports": [],
    }

    clients = {}

    if config.openai_api_key:
        clients["openai"] = AsyncOpenAI(api_key=config.openai_api_key)

    if config.self_hosted_url:
        clients["self_hosted"] = AsyncOpenAI(
            base_url=f"{config.self_hosted_url}/v1",
            api_key="dummy",
        )

    for prompt in config.prompts:
        print(f"\n{'='*60}")
        print(f"Prompt: {prompt[:50]}...")
        print(f"{'='*60}")

        if "openai" in clients:
            for model in ["gpt-4o-mini"]:
                print(f"\nBenchmarking OpenAI {model}...")
                model_results = []

                for _ in range(config.warmup_runs):
                    await benchmark_openai(clients["openai"], model, prompt, config)

                for i in range(config.num_runs):
                    result = await benchmark_openai(
                        clients["openai"], model, prompt, config
                    )
                    model_results.append(result)
                    print(
                        f"  Run {i+1}: TTFT={result.ttft_ms:.0f}ms, "
                        f"Total={result.total_ms:.0f}ms, TPS={result.tps:.1f}"
                    )

                report = aggregate_results(model_results)
                report["prompt_preview"] = prompt[:50]
                results["reports"].append(report)

        if "self_hosted" in clients:
            print("\nBenchmarking Self-Hosted...")
            model_results = []
            model_name = os.getenv("MODEL_NAME", "qwen3-8b-awq")

            for _ in range(config.warmup_runs):
                await benchmark_self_hosted(
                    clients["self_hosted"], model_name, prompt, config
                )

            for i in range(config.num_runs):
                result = await benchmark_self_hosted(
                    clients["self_hosted"], model_name, prompt, config
                )
                model_results.append(result)
                print(
                    f"  Run {i+1}: TTFT={result.ttft_ms:.0f}ms, "
                    f"Total={result.total_ms:.0f}ms, TPS={result.tps:.1f}"
                )

            report = aggregate_results(model_results)
            report["prompt_preview"] = prompt[:50]
            results["reports"].append(report)

    return results


def print_summary(results: dict):
    """Print benchmark summary."""
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    by_provider = {}
    for report in results["reports"]:
        provider = report["provider"]
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(report)

    for provider, reports in by_provider.items():
        print(f"\n{provider}:")
        print("-" * 40)

        valid_reports = [r for r in reports if "avg_ttft_ms" in r]
        if valid_reports:
            avg_ttft = statistics.mean(r["avg_ttft_ms"] for r in valid_reports)
            avg_total = statistics.mean(r["avg_total_ms"] for r in valid_reports)
            avg_tps = statistics.mean(r["avg_tps"] for r in valid_reports)
            total_cost = sum(r["total_cost_usd"] for r in valid_reports)

            print(f"  Avg TTFT:     {avg_ttft:>8.1f} ms")
            print(f"  Avg Total:    {avg_total:>8.1f} ms")
            print(f"  Avg TPS:      {avg_tps:>8.1f} tokens/sec")
            print(f"  Total Cost:   ${total_cost:>7.4f}")


def save_results(results: dict, output_dir: str = "benchmarks/results"):
    """Save benchmark results to JSON."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(output_dir) / f"benchmark_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")


async def main():
    """Main entry point."""
    config = BenchmarkConfig()

    if not config.self_hosted_url and not config.openai_api_key:
        print("Error: Could not determine API URL or API key.")
        print("\nFor self-hosted LLM, set:")
        print("  export SELF_HOSTED_URL=https://llm-api-xxx.run.app")
        print("  # or")
        print("  export LLM_API_URL=https://llm-api-xxx.run.app")
        print("\nTo find your service URL, run:")
        cmd = (
            "gcloud run services describe llm-api --region "
            "asia-southeast1 --format 'value(status.url)'"
        )
        print(f"  {cmd}")
        print("\nFor OpenAI comparison, also set:")
        print("  export OPENAI_API_KEY=sk-...")
        return

    print("Starting LLM Latency Benchmark...")
    print(f"Configuration: {config.num_runs} runs, {config.max_tokens} max tokens")

    results = await run_benchmark(config)
    print_summary(results)
    save_results(results)


if __name__ == "__main__":
    asyncio.run(main())
