#!/usr/bin/env python
# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges."
# 性能基准测试

import time
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentos_cta.utils.token_counter import TokenCounter
from agentos_cta.utils.latency_monitor import LatencyMonitor

async def test_token_counter():
    counter = TokenCounter("gpt-4")
    text = "Hello, world! " * 1000
    start = time.time()
    count = counter.count_tokens(text)
    elapsed = time.time() - start
    print(f"TokenCounter: {count} tokens in {elapsed:.4f}s")

async def test_latency_monitor():
    monitor = LatencyMonitor()
    for _ in range(100):
        monitor.record(50 + (time.time() % 10))
    p95 = monitor.p95()
    print(f"LatencyMonitor: p95 = {p95:.2f}ms")

async def main():
    print("Running benchmarks...")
    await test_token_counter()
    await test_latency_monitor()
    # 可添加更多测试

if __name__ == "__main__":
    asyncio.run(main())