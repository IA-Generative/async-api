from datetime import datetime
from typing import Annotated

from fastapi import Depends
from prometheus_client import Gauge, Histogram

from api.repositories import MetricsTaskRepository
from api.schemas.enum import TaskStatus

# Constants for Prometheus metrics
INF: float = float("inf")
S: float = 1.0
MN: float = 60.0 * S
H: float = 60.0 * MN


class MetricsService:
    """Service for managing Prometheus metrics related to tasks.
    This service provides methods to update custom metrics for tasks, including
    pending, running, success, and failure counts, as well as latency histograms.
    It uses the MetricsTaskRepository to fetch task data from the database.
    """

    # Custom metrics
    TASKS_PENDING_COUNT = Gauge("tasks_pending_count", "Tasks pending count", ["service"])
    TASKS_IN_PROGRESS_COUNT = Gauge("tasks_in_progress_count", "Tasks in_progress count", ["service"])
    TASKS_SUCCESS_COUNT = Gauge("tasks_success_count", "Tasks success count", ["service"])
    TASKS_FAILURE_COUNT = Gauge("tasks_failure_count", "Tasks failurecount", ["service"])

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
        ["service"],
        buckets=TASKS_LATENCY_BUCKETS,
    )
    TASKS_LATENCY_RUNNING = Histogram(
        "tasks_latency_running",
        "Tasks latency running (s)",
        ["service"],
        buckets=TASKS_LATENCY_BUCKETS,
    )

    def __init__(
        self,
        metrics_repository: Annotated[MetricsTaskRepository, Depends(MetricsTaskRepository)],
    ) -> None:
        self.taskRepo = metrics_repository

    async def update_custom_metrics(self) -> None:
        latency_result = await self.taskRepo.running_and_pending_tasks()
        now = datetime.now()
        self.TASKS_LATENCY_RUNNING.clear()
        self.TASKS_LATENCY_PENDING.clear()
        for metric in latency_result:
            if metric.status == TaskStatus.PENDING and metric.submition_date:
                self.TASKS_LATENCY_PENDING.labels(service=metric.service).observe(
                    (now - metric.submition_date).total_seconds(),
                )
            elif metric.status == TaskStatus.IN_PROGRESS and metric.start_date:
                self.TASKS_LATENCY_RUNNING.labels(service=metric.service).observe(
                    (now - metric.start_date).total_seconds(),
                )

        count_result = await self.taskRepo.count_tasks_per_status_and_service()
        for metric in count_result:
            if metric.status == TaskStatus.PENDING:
                self.TASKS_PENDING_COUNT.labels(service=metric.service).set(metric.count)
            elif metric.status == TaskStatus.IN_PROGRESS:
                self.TASKS_IN_PROGRESS_COUNT.labels(service=metric.service).set(metric.count)
            elif metric.status == TaskStatus.SUCCESS:
                self.TASKS_SUCCESS_COUNT.labels(service=metric.service).set(metric.count)
            elif metric.status == TaskStatus.FAILURE:
                self.TASKS_FAILURE_COUNT.labels(service=metric.service).set(metric.count)
