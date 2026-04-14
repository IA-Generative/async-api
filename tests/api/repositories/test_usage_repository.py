import uuid
from datetime import datetime, timedelta

import pytest

from api.models.task import Task
from api.repositories.usage_repository import UsageRepository
from api.schemas.enum import TaskStatus


async def _create_task(
    session,  # noqa: ANN001
    client_id: str,
    service: str,
    status: str,
    submition_date: datetime | None = None,
) -> None:
    task = Task(
        task_id=str(uuid.uuid4()),
        client_id=client_id,
        service=service,
        status=status,
        request={},
        submition_date=submition_date or datetime.now(),
    )
    session.add(task)
    await session.commit()


@pytest.mark.asyncio
async def test_count_usage_by_client(async_db_session) -> None:  # noqa: ANN001
    for _ in range(3):
        await _create_task(async_db_session, "client_a", "ocr", TaskStatus.SUCCESS)
    for _ in range(2):
        await _create_task(async_db_session, "client_a", "ocr", TaskStatus.FAILURE)
    for _ in range(5):
        await _create_task(async_db_session, "client_a", "translation", TaskStatus.SUCCESS)
    await _create_task(async_db_session, "client_a", "translation", TaskStatus.FAILURE)

    repo = UsageRepository(async_db_session)
    since = datetime.now() - timedelta(days=30)
    results = await repo.count_usage_by_client(client_id="client_a", since=since)

    by_svc = {}
    for r in results:
        by_svc.setdefault(r.service, {})[r.status] = r.count

    assert by_svc["ocr"][TaskStatus.SUCCESS] == 3
    assert by_svc["ocr"][TaskStatus.FAILURE] == 2
    assert by_svc["translation"][TaskStatus.SUCCESS] == 5
    assert by_svc["translation"][TaskStatus.FAILURE] == 1


@pytest.mark.asyncio
async def test_count_usage_filters_by_date(async_db_session) -> None:  # noqa: ANN001
    old_date = datetime.now() - timedelta(days=60)
    recent_date = datetime.now() - timedelta(days=5)

    for _ in range(3):
        await _create_task(async_db_session, "client_a", "ocr", TaskStatus.SUCCESS, submition_date=old_date)
    for _ in range(2):
        await _create_task(async_db_session, "client_a", "ocr", TaskStatus.SUCCESS, submition_date=recent_date)

    repo = UsageRepository(async_db_session)
    since = datetime.now() - timedelta(days=30)
    results = await repo.count_usage_by_client(client_id="client_a", since=since)

    assert len(results) == 1
    assert results[0].service == "ocr"
    assert results[0].status == TaskStatus.SUCCESS
    assert results[0].count == 2


@pytest.mark.asyncio
async def test_count_usage_excludes_pending_and_in_progress(async_db_session) -> None:  # noqa: ANN001
    await _create_task(async_db_session, "client_a", "ocr", TaskStatus.PENDING)
    await _create_task(async_db_session, "client_a", "ocr", TaskStatus.IN_PROGRESS)
    await _create_task(async_db_session, "client_a", "ocr", TaskStatus.SUCCESS)

    repo = UsageRepository(async_db_session)
    since = datetime.now() - timedelta(days=30)
    results = await repo.count_usage_by_client(client_id="client_a", since=since)

    assert len(results) == 1
    assert results[0].status == TaskStatus.SUCCESS
    assert results[0].count == 1


@pytest.mark.asyncio
async def test_count_usage_filters_by_client(async_db_session) -> None:  # noqa: ANN001
    await _create_task(async_db_session, "client_a", "ocr", TaskStatus.SUCCESS)
    await _create_task(async_db_session, "client_b", "ocr", TaskStatus.SUCCESS)

    repo = UsageRepository(async_db_session)
    since = datetime.now() - timedelta(days=30)
    results = await repo.count_usage_by_client(client_id="client_a", since=since)

    assert len(results) == 1
    assert results[0].count == 1


@pytest.mark.asyncio
async def test_count_usage_returns_empty_for_unknown_client(async_db_session) -> None:  # noqa: ANN001
    await _create_task(async_db_session, "client_a", "ocr", TaskStatus.SUCCESS)

    repo = UsageRepository(async_db_session)
    since = datetime.now() - timedelta(days=30)
    results = await repo.count_usage_by_client(client_id="unknown", since=since)

    assert results == []
