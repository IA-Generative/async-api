from datetime import datetime
from typing import Annotated

from fastapi import Depends

from api.repositories import MetricsTaskRepository
from api.repositories.metrics_repository import PendingAndRunningTaskView, TaskCountByStatusAndServiceView
from api.schemas.enum import TaskStatus
from api.services.metrics_constants import (
    TASKS_FAILURE_COUNT,
    TASKS_IN_PROGRESS_COUNT,
    TASKS_LATENCY_PENDING,
    TASKS_LATENCY_RUNNING,
    TASKS_PENDING_COUNT,
    TASKS_SUBMITTED_TOTAL,
    TASKS_SUCCESS_COUNT,
)


class MetricsService:
    """Service for managing Prometheus metrics related to tasks.
    This service provides methods to update custom metrics for tasks, including
    pending, running, success, and failure counts, as well as latency histograms.
    It uses the MetricsTaskRepository to fetch task data from the database.
    """

    @staticmethod
    def increment_tasks_submitted(service: str, client_id: str) -> None:
        TASKS_SUBMITTED_TOTAL.labels(service=service, client_id=client_id).inc()

    def __init__(
        self,
        metrics_repository: Annotated[MetricsTaskRepository, Depends(MetricsTaskRepository)],
    ) -> None:
        self.taskRepo = metrics_repository

    async def update_custom_metrics(self) -> None:
        latency_result = await self.taskRepo.running_and_pending_tasks()
        now = datetime.now()
        TASKS_LATENCY_RUNNING.clear()
        TASKS_LATENCY_PENDING.clear()
        for metric in latency_result:
            self._observe_task_latency(metric, now)

        TASKS_PENDING_COUNT.clear()
        TASKS_IN_PROGRESS_COUNT.clear()
        TASKS_SUCCESS_COUNT.clear()
        TASKS_FAILURE_COUNT.clear()

        count_result = await self.taskRepo.count_tasks_per_status_and_service()
        for metric in count_result:
            self._update_task_count_gauge(metric)

    def _observe_task_latency(self, metric: PendingAndRunningTaskView, now: datetime) -> None:
        labels = {"service": metric.service, "client_id": metric.client_id}
        match metric.status:
            case TaskStatus.PENDING if metric.submition_date:
                TASKS_LATENCY_PENDING.labels(**labels).observe(
                    (now - metric.submition_date).total_seconds(),
                )
            case TaskStatus.IN_PROGRESS if metric.start_date:
                TASKS_LATENCY_RUNNING.labels(**labels).observe(
                    (now - metric.start_date).total_seconds(),
                )

    def _update_task_count_gauge(self, metric: TaskCountByStatusAndServiceView) -> None:
        labels = {"service": metric.service, "client_id": metric.client_id}
        match metric.status:
            case TaskStatus.PENDING:
                TASKS_PENDING_COUNT.labels(**labels).set(metric.count)
            case TaskStatus.IN_PROGRESS:
                TASKS_IN_PROGRESS_COUNT.labels(**labels).set(metric.count)
            case TaskStatus.SUCCESS:
                TASKS_SUCCESS_COUNT.labels(**labels).set(metric.count)
            case TaskStatus.FAILURE:
                TASKS_FAILURE_COUNT.labels(**labels).set(metric.count)
