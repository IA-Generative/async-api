import pytest
from prometheus_client import Gauge

from api.repositories.metrics_repository import TaskCountByStatusAndServiceView
from api.schemas.enum import TaskStatus
from api.services.metrics_service import MetricsService


@pytest.fixture(autouse=True)
def _clean_gauges() -> None:
    """Clear all task count gauges before each test."""
    MetricsService.TASKS_PENDING_COUNT.clear()
    MetricsService.TASKS_IN_PROGRESS_COUNT.clear()
    MetricsService.TASKS_SUCCESS_COUNT.clear()
    MetricsService.TASKS_FAILURE_COUNT.clear()


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
        assert self._get_gauge_value(MetricsService.TASKS_PENDING_COUNT) == 5

    def test_in_progress_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.IN_PROGRESS, 3)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(MetricsService.TASKS_IN_PROGRESS_COUNT) == 3

    def test_success_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.SUCCESS, 10)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(MetricsService.TASKS_SUCCESS_COUNT) == 10

    def test_failure_status(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric(TaskStatus.FAILURE, 7)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(MetricsService.TASKS_FAILURE_COUNT) == 7

    def test_unknown_status_does_nothing(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric = self._build_metric("unknown_status", 99)
        service._update_task_count_gauge(metric)
        assert self._get_gauge_value(MetricsService.TASKS_PENDING_COUNT) == 0
        assert self._get_gauge_value(MetricsService.TASKS_IN_PROGRESS_COUNT) == 0
        assert self._get_gauge_value(MetricsService.TASKS_SUCCESS_COUNT) == 0
        assert self._get_gauge_value(MetricsService.TASKS_FAILURE_COUNT) == 0

    def test_different_clients(self) -> None:
        service = MetricsService.__new__(MetricsService)
        metric_a = self._build_metric(TaskStatus.PENDING, 2, client_id="astree")
        metric_b = self._build_metric(TaskStatus.PENDING, 8, client_id="prisme")
        service._update_task_count_gauge(metric_a)
        service._update_task_count_gauge(metric_b)
        assert self._get_gauge_value(MetricsService.TASKS_PENDING_COUNT, client_id="astree") == 2
        assert self._get_gauge_value(MetricsService.TASKS_PENDING_COUNT, client_id="prisme") == 8
