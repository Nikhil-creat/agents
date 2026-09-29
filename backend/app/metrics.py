from prometheus_client import Counter, Histogram
TOOL_CALLS = Counter("agents_tool_calls_total", "Tool calls", ["tool"])
TOOL_LAT = Histogram("agents_tool_latency_seconds", "Tool latency", ["tool"])
