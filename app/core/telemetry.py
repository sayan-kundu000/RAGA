"""Execution latency telemetry and performance profiling."""

import time
from contextlib import contextmanager
from typing import Generator
from pydantic import BaseModel, Field


class TelemetryMetrics(BaseModel):
    """Telemetry performance metrics returned in API responses."""

    retrieval_latency_ms: float = Field(
        ...,
        description="Time taken to perform hybrid dense-sparse search and parent document resolution in milliseconds",
        ge=0.0
    )
    rerank_latency_ms: float = Field(
        ...,
        description="Time taken to compress and re-rank candidate documents via Cohere in milliseconds",
        ge=0.0
    )
    generation_latency_ms: float = Field(
        ...,
        description="Time taken for LLM generation with memory context in milliseconds",
        ge=0.0
    )
    total_latency_ms: float = Field(
        ...,
        description="Total round-trip request execution latency in milliseconds",
        ge=0.0
    )


class LatencyTimer:
    """Utility class to measure execution durations with high precision."""

    def __init__(self) -> None:
        self.retrieval_latency_ms: float = 0.0
        self.rerank_latency_ms: float = 0.0
        self.generation_latency_ms: float = 0.0
        self._start_total: float = time.perf_counter()

    @contextmanager
    def measure_retrieval(self) -> Generator[None, None, None]:
        """Context manager to measure retrieval execution latency."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.retrieval_latency_ms = round(max((time.perf_counter() - t0) * 1000, 0.01), 2)

    @contextmanager
    def measure_rerank(self) -> Generator[None, None, None]:
        """Context manager to measure re-ranking execution latency."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.rerank_latency_ms = round(max((time.perf_counter() - t0) * 1000, 0.01), 2)

    @contextmanager
    def measure_generation(self) -> Generator[None, None, None]:
        """Context manager to measure generation execution latency."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.generation_latency_ms = round(max((time.perf_counter() - t0) * 1000, 0.01), 2)

    def finalize(self) -> TelemetryMetrics:
        """Calculate total execution time and compile telemetry metrics."""
        total_ms = round(max((time.perf_counter() - self._start_total) * 1000, 0.01), 2)
        # Ensure total is at least the sum of components
        component_sum = round(self.retrieval_latency_ms + self.rerank_latency_ms + self.generation_latency_ms, 2)
        if total_ms < component_sum:
            total_ms = component_sum

        return TelemetryMetrics(
            retrieval_latency_ms=self.retrieval_latency_ms,
            rerank_latency_ms=self.rerank_latency_ms,
            generation_latency_ms=self.generation_latency_ms,
            total_latency_ms=total_ms
        )
