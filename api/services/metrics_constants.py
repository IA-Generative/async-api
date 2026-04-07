from prometheus_client import Counter, Gauge, Histogram

# Time unit constants
INF: float = float("inf")
S: float = 1.0
MN: float = 60.0 * S
H: float = 60.0 * MN

# Gauges
TASKS_PENDING_COUNT = Gauge("tasks_pending_count", "Tasks pending count", ["service", "client_id"])
TASKS_IN_PROGRESS_COUNT = Gauge("tasks_in_progress_count", "Tasks in_progress count", ["service", "client_id"])
TASKS_SUCCESS_COUNT = Gauge("tasks_success_count", "Tasks success count", ["service", "client_id"])
TASKS_FAILURE_COUNT = Gauge("tasks_failure_count", "Tasks failurecount", ["service", "client_id"])

# Counters
TASKS_SUBMITTED_TOTAL = Counter("tasks_submitted_total", "Total tasks submitted", ["service", "client_id"])

# Histograms
TASKS_LATENCY_BUCKETS = (
    5.0 * S,
    30.0 * S,
    1 * MN,
    2 * MN,
    5 * MN,
    10 * MN,
    30 * MN,
    1 * H,
    INF,
)
TASKS_LATENCY_PENDING = Histogram(
    "tasks_latency_pending",
    "Tasks latency pending (s)",
    ["service", "client_id"],
    buckets=TASKS_LATENCY_BUCKETS,
)
TASKS_LATENCY_RUNNING = Histogram(
    "tasks_latency_running",
    "Tasks latency running (s)",
    ["service", "client_id"],
    buckets=TASKS_LATENCY_BUCKETS,
)
