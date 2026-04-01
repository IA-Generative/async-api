from unittest.mock import AsyncMock

import pytest

from api.repositories.usage_repository import UsageCountView
from api.schemas.enum import TaskStatus
from api.services.usage_service import UsageService


@pytest.fixture
def usage_repository_mock() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_get_client_usage_aggregates_data(usage_repository_mock: AsyncMock) -> None:
    usage_repository_mock.count_usage_by_client.return_value = [
        UsageCountView(service="ocr", status=TaskStatus.SUCCESS, count=10),
        UsageCountView(service="ocr", status=TaskStatus.FAILURE, count=2),
        UsageCountView(service="translation", status=TaskStatus.SUCCESS, count=5),
    ]

    service = UsageService(usage_repository=usage_repository_mock)
    result = await service.get_client_usage(client_id="client_a", days=30)

    assert result.client_id == "client_a"
    assert result.period_days == 30
    assert len(result.services) == 2

    ocr = next(s for s in result.services if s.service == "ocr")
    assert ocr.success_count == 10
    assert ocr.failure_count == 2

    translation = next(s for s in result.services if s.service == "translation")
    assert translation.success_count == 5
    assert translation.failure_count == 0


@pytest.mark.asyncio
async def test_get_client_usage_empty_result(usage_repository_mock: AsyncMock) -> None:
    usage_repository_mock.count_usage_by_client.return_value = []

    service = UsageService(usage_repository=usage_repository_mock)
    result = await service.get_client_usage(client_id="unknown", days=30)

    assert result.client_id == "unknown"
    assert result.period_days == 30
    assert result.services == []


@pytest.mark.asyncio
async def test_get_client_usage_custom_days(usage_repository_mock: AsyncMock) -> None:
    usage_repository_mock.count_usage_by_client.return_value = []

    service = UsageService(usage_repository=usage_repository_mock)
    await service.get_client_usage(client_id="client_a", days=7)

    call_kwargs = usage_repository_mock.count_usage_by_client.call_args.kwargs
    assert call_kwargs["client_id"] == "client_a"
    # Verify 'since' was passed (computed from days=7)
    assert "since" in call_kwargs


@pytest.mark.asyncio
async def test_get_client_usage_only_failures(usage_repository_mock: AsyncMock) -> None:
    usage_repository_mock.count_usage_by_client.return_value = [
        UsageCountView(service="ocr", status=TaskStatus.FAILURE, count=3),
    ]

    service = UsageService(usage_repository=usage_repository_mock)
    result = await service.get_client_usage(client_id="client_a", days=30)

    assert len(result.services) == 1
    assert result.services[0].success_count == 0
    assert result.services[0].failure_count == 3


@pytest.mark.asyncio
async def test_get_client_usage_services_sorted(usage_repository_mock: AsyncMock) -> None:
    usage_repository_mock.count_usage_by_client.return_value = [
        UsageCountView(service="z_service", status=TaskStatus.SUCCESS, count=1),
        UsageCountView(service="a_service", status=TaskStatus.SUCCESS, count=2),
    ]

    service = UsageService(usage_repository=usage_repository_mock)
    result = await service.get_client_usage(client_id="client_a", days=30)

    assert result.services[0].service == "a_service"
    assert result.services[1].service == "z_service"
