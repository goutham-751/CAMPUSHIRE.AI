import time
from typing import Dict, Any

# Global state for telemetry
# In a real production system with multiple workers, this would be backed by Redis or similar.
class TelemetryState:
    def __init__(self):
        self.start_time = time.time()
        self.total_tokens = 14200  # Start with a base mock value or 0
        self.last_latency_ms = 0.0

global_telemetry = TelemetryState()

def get_telemetry_data() -> Dict[str, Any]:
    uptime_seconds = time.time() - global_telemetry.start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return {
        "api_latency_ms": int(global_telemetry.last_latency_ms),
        "total_tokens": global_telemetry.total_tokens,
        "uptime": uptime_str,
        "status": "Active" if global_telemetry.last_latency_ms < 500 else "Degraded"
    }

def record_api_call(latency_ms: float, is_llm: bool = False):
    global_telemetry.last_latency_ms = latency_ms
    if is_llm:
        # Increment tokens by a simulated amount if it's an LLM heavy route
        global_telemetry.total_tokens += 125
