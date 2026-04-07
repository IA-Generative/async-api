from datetime import datetime, timedelta

import pytest
from prometheus_client import Gauge, Histogram

from api.repositories.metrics_repository import PendingAndRunningTaskView, TaskCountByStatusAndServiceView
from api.schemas.enum import TaskStatus
from api.services.metrics_constants import (
    TASKS_FAILURE_COUNT,
    TASKS_IN_PROGRESS_COUNT,
    TASKS_LATENCY_PENDING,
    TASKS_LATENCY_RUNNING,
    TASKS_PENDING_COUNT,
    TASKS_SUCCESS_COUNT,
)
from api.services.metrics_service import MetricsService


@pytest.fixture(autouse=True)
def _clean_metrics() -> None:
    """Clear all metrics before each test."""
    TASKS_PENDING_COUNT.clear()
    TASKS_IN_PROGRESS_COUNT.clear()
    TASKS_SUCCESS_COUNT.clear()
    TASKS_FAILURE_COUNT.clear()
    TASKS_LATENCY_PENDING.clear()
    TASKS_LATENCY_RUNNING.clear()


class TestUpdateTaskCountGauge:
    def _build_metric(
        self, status: str, count: int, service: str = "svc1", client_id: str = "client1",
    ) -> TaskCountByStatusAndServiceView:
        return TaskCountByStatusAndServiceView(
            service=service, status=status, client_id=client_id, count=count,
        )

    def _get_gauge_value(self, gauge: Gauge, service: str = "svc1", client_id: str = "client1") -> float:
        return gauge.labels(service=service, client_id=client_id)._value.get()

    def test_pending_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.PENDING, 5)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(TASKS_PENDING_COUNT) == 5

    def test_in_progress_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.IN_PROGRESS, 3)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(TASKS_IN_PROGRESS_COUNT) == 3

    def test_success_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.SUCCESS, 10)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(TASKS_SUCCESS_COUNT) == 10

    def test_failure_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.FAILURE, 7)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(TASKS_FAILURE_COUNT) == 7

    def test_unknown_status_does_nothing(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric("unknown_status", 99)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(TASKS_PENDING_COUNT) == 0
        assert self._get_gauge_value(TASKS_IN_PROGRESS_COUNT) == 0
        assert self._get_gauge_value(TASKS_SUCCESS_COUNT) == 0
        assert self._get_gauge_value(TASKS_FAILURE_COUNT) == 0

    def test_different_clients(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric_a = self._build_metric(TaskStatus.PENDING, 2, client_id="astree")
        metric_b = self._build_metric(TaskStatus.PENDING, 8, client_id="prisme")
        service._update_task_count_gauge(metric_a)
        service._update_task_count_gauge(metric_b)
        assert self._get_gauge_value(TASKS_PENDING_COUNT, client_id="astree") == 2
        assert self._get_gauge_value(TASKS_PENDING_COUNT, client_id="prisme") == 8


class TestObserveTaskLatency:
    def _build_metric(
        self,
        status: str,
        service: str = "svc1",
        client_id: str = "client1",
        submition_date: datetime | None = None,
        start_date: datetime | None = None,
    ) -> PendingAndRunningTaskView:
        return PendingAndRunningTaskView(
            service=service, status=status, client_id=client_id,
            submition_date=submition_date, start_date=start_date,
        )

    def _get_histogram_count(
        self, histogram: Histogram, service: str = "svc1", client_id: str = "client1",
    ) -> int:
        return histogram.labels(service=service, client_id=client_id)._sum._value

    def test_pending_with_submition_date(self) -> None:
        svc = MetricsService.__new__(MetricsService)
        now = datetime.now()
        metric = self._build_metric(TaskStatus.PENDING, submition_date=now - timedelta(seconds=10))
        svc._observe_task_latency(metric, now)
        count = TASKS_LATENCY_PENDING.labels(service="svc1", client_id="client1")._sum.get()
        assert count == pytest.approx(10.0, abs=0.1)

    def test_pending_without_submition_date_does_nothing(self) -> None:
        svc = MetricsService.__new__(MetricsService)
        now = datetime.now()
        metric = self._build_metric(TaskStatus.PENDING, submition_date=None)
        svc._observe_task_latency(metric, now)
        count = TASKS_LATENCY_PENDING.labels(service="svc1", client_id="client1")._sum.get()
        assert count == pytest.approx(0.0)

    def test_in_progress_with_start_date(self) -> None:
        svc = MetricsService.__new__(MetricsService)
        now = datetime.now()
        metric = self._build_metric(TaskStatus.IN_PROGRESS, start_date=now - timedelta(seconds=30))
        svc._observe_task_latency(metric, now)
        count = TASKS_LATENCY_RUNNING.labels(service="svc1", client_id="client1")._sum.get()
        assert count == pytest.approx(30.0, abs=0.1)

    def test_in_progress_without_start_date_does_nothing(self) -> None:
        svc = MetricsService.__new__(MetricsService)
        now = datetime.now()
        metric = self._build_metric(TaskStatus.IN_PROGRESS, start_date=None)
        svc._observe_task_latency(metric, now)
        count = TASKS_LATENCY_RUNNING.labels(service="svc1", client_id="client1")._sum.get()
        assert count == pytest.approx(0.0)

    def test_different_clients(self) -> None:
        svc = MetricsService.__new__(MetricsService)
        now = datetime.now()
        metric_a = self._build_metric(
            TaskStatus.PENDING, client_id="astree", submition_date=now - timedelta(seconds=5),
        )
        metric_b = self._build_metric(
            TaskStatus.PENDING, client_id="prisme", submition_date=now - timedelta(seconds=20),
        )
        svc._observe_task_latency(metric_a, now)
        svc._observe_task_latency(metric_b, now)
        sum_a = TASKS_LATENCY_PENDING.labels(service="svc1", client_id="astree")._sum.get()
        sum_b = TASKS_LATENCY_PENDING.labels(service="svc1", client_id="prisme")._sum.get()
        assert sum_a == pytest.approx(5.0, abs=0.1)
        assert sum_b == pytest.approx(20.0, abs=0.1)
