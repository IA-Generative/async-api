from datetime import datetime
from typing import Annotated

from fastapi import Depends
from prometheus_client import Counter, Gauge, Histogram

from api.repositories import MetricsTaskRepository
from api.repositories.metrics_repository import PendingAndRunningTaskView, TaskCountByStatusAndServiceView
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
    TASKS_PENDING_COUNT = Gauge("tasks_pending_count", "Tasks pending count", ["service", "client_id"])
    TASKS_IN_PROGRESS_COUNT = Gauge("tasks_in_progress_count", "Tasks in_progress count", ["service", "client_id"])
    TASKS_SUCCESS_COUNT = Gauge("tasks_success_count", "Tasks success count", ["service", "client_id"])
    TASKS_FAILURE_COUNT = Gauge("tasks_failure_count", "Tasks failurecount", ["service", "client_id"])

    TASKS_SUBMITTED_TOTAL = Counter("tasks_submitted_total", "Total tasks submitted", ["service", "client_id"])

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

    @classmethod
    def increment_tasks_submitted(cls, service: str, client_id: str) -> None:
        cls.TASKS_SUBMITTED_TOTAL.labels(service=service, client_id=client_id).inc()

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
            self._observe_task_latency(metric, now)

        self.TASKS_PENDING_COUNT.clear()
        self.TASKS_IN_PROGRESS_COUNT.clear()
        self.TASKS_SUCCESS_COUNT.clear()
        self.TASKS_FAILURE_COUNT.clear()

        count_result = await self.taskRepo.count_tasks_per_status_and_service()
        for metric in count_result:
            self._update_task_count_gauge(metric)

    def _observe_task_latency(self, metric: PendingAndRunningTaskView, now: datetime) -> None:
        labels = {"service": metric.service, "client_id": metric.client_id}
        match metric.status:
            case TaskStatus.PENDING if metric.submition_date:
                self.TASKS_LATENCY_PENDING.labels(**labels).observe(
                    (now - metric.submition_date).total_seconds(),
                )
            case TaskStatus.IN_PROGRESS if metric.start_date:
                self.TASKS_LATENCY_RUNNING.labels(**labels).observe(
                    (now - metric.start_date).total_seconds(),
                )

    def _update_task_count_gauge(self, metric: TaskCountByStatusAndServiceView) -> None:
        labels = {"service": metric.service, "client_id": metric.client_id}
        match metric.status:
            case TaskStatus.PENDING:
                self.TASKS_PENDING_COUNT.labels(**labels).set(metric.count)
            case TaskStatus.IN_PROGRESS:
                self.TASKS_IN_PROGRESS_COUNT.labels(**labels).set(metric.count)
            case TaskStatus.SUCCESS:
                self.TASKS_SUCCESS_COUNT.labels(**labels).set(metric.count)
            case TaskStatus.FAILURE:
                self.TASKS_FAILURE_COUNT.labels(**labels).set(metric.count)
