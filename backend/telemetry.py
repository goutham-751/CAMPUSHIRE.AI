"""
Live application telemetry — request latency, request counts, and real LLM token usage.

Token counts are incremented only from provider usage objects (e.g. Groq),
never by fake per-route constants.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional


class TelemetryState:
    def __init__(self):
        self.start_time = time.time()
        self.total_tokens = 0
        self.last_latency_ms = 0.0
        self.request_count = 0
        self.llm_calls = 0


global_telemetry = TelemetryState()


def get_telemetry_data() -> Dict[str, Any]:
    uptime_seconds = time.time() - global_telemetry.start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return {
        "api_latency_ms": int(global_telemetry.last_latency_ms),
        "total_tokens": int(global_telemetry.total_tokens),
        "uptime": uptime_str,
        "status": "Active" if global_telemetry.last_latency_ms < 5000 else "Degraded",
        "request_count": int(global_telemetry.request_count),
        "llm_calls": int(global_telemetry.llm_calls),
    }


def record_api_call(latency_ms: float, is_llm: bool = False):
    """Record HTTP latency. Does not fabricate token counts."""
    global_telemetry.last_latency_ms = latency_ms
    global_telemetry.request_count += 1


def record_llm_usage(usage: Any = None, total_tokens: Optional[int] = None) -> None:
    """Accumulate real token usage from an LLM provider response."""
    tokens = 0
    if total_tokens is not None:
        tokens = int(total_tokens)
    elif usage is not None:
        tokens = int(getattr(usage, "total_tokens", None) or 0)
        if tokens <= 0:
            prompt = int(getattr(usage, "prompt_tokens", None) or 0)
            completion = int(getattr(usage, "completion_tokens", None) or 0)
            tokens = prompt + completion
    if tokens > 0:
        global_telemetry.total_tokens += tokens
    global_telemetry.llm_calls += 1
