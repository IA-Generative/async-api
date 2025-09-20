import asyncio

import pytest

from api.repositories.task_repository import TaskRepository
from api.schemas.enum import TaskStatus
from api.schemas.task import TaskInfo


@pytest.mark.asyncio
async def test_should_create_new_task(async_db_session) -> None:  # noqa: ANN001
    repo = TaskRepository(async_db_session)
    task_info = TaskInfo(
        task_id="test_task",
        client_id="test_client",
        service="test_service",
        status=TaskStatus.PENDING,
        request={},
        callback=None,
    )
    task = await repo.create_task_record(task_info)
    assert task is not None


@pytest.mark.asyncio
async def test_get_task_by_id(async_db_session) -> None:  # noqa: ANN001
    repo = TaskRepository(async_db_session)
    task_info1 = TaskInfo(
        task_id="test_task1",
        client_id="test_client1",
        service="test_service1",
        status=TaskStatus.PENDING,
        request={},
        callback=None,
    )
    task_info2 = TaskInfo(
        task_id="test_task2",
        client_id="test_client2",
        service="test_service2",
        status=TaskStatus.PENDING,
        request={},
        callback=None,
    )
    await repo.create_task_record(task_info1)
    await repo.create_task_record(task_info2)

    task = await repo.get_task_by_id("test_task2", "test_service2")
    assert task is not None
    assert str(task.client_id) == "test_client2"


@pytest.mark.asyncio
async def test_get_task_position_by_id(async_db_session) -> None:  # noqa: ANN001
    repo = TaskRepository(async_db_session)
    task_info = TaskInfo(
        task_id="test_task_run",
        client_id="test_task_run",
        service="svc",
        status=TaskStatus.IN_PROGRESS,
        request={},
        callback=None,
    )
    await repo.create_task_record(task_info)
    for i in range(3):
        task_info = TaskInfo(
            task_id=f"test_task{i}",
            client_id=f"test_task{i}",
            service="svc",
            status=TaskStatus.PENDING,
            request={},
            callback=None,
        )
        await repo.create_task_record(task_info)

    await asyncio.sleep(0.1)

    added = TaskInfo(
        task_id="test_added",
        client_id="test_added",
        service="svc",
        status=TaskStatus.PENDING,
        request={},
        callback=None,
    )
    await repo.create_task_record(added)
    position = await repo.get_task_position_by_id("test_added", "svc")
    assert position is not None
    assert position == 4


@pytest.mark.asyncio
async def test_count_pending_tasks_for_service(async_db_session) -> None:  # noqa: ANN001
    repo = TaskRepository(async_db_session)
    # 3 PENDING
    for i in range(3):
        task_info = TaskInfo(
            task_id=f"test_task{i}",
            client_id="test_task{i}",
            service="svc",
            status=TaskStatus.PENDING,
            request={},
            callback=None,
        )
        await repo.create_task_record(task_info)
    # 1 RUNNING
    task_running = TaskInfo(
        task_id="test_task_running",
        client_id="test_task_running",
        service="svc",
        status=TaskStatus.IN_PROGRESS,
        request={},
        callback=None,
    )
    await repo.create_task_record(task_running)
    # 1 Another service
    task_other = TaskInfo(
        task_id="test_task_task_other",
        client_id="test_task_running",
        service="task_other",
        status=TaskStatus.IN_PROGRESS,
        request={},
        callback=None,
    )
    await repo.create_task_record(task_other)

    nbr = await repo.count_pending_tasks_for_service("svc")
    assert nbr == 3


@pytest.mark.asyncio
async def test_count_pending_tasks_for_service_and_client(async_db_session) -> None:  # noqa: ANN001
    repo = TaskRepository(async_db_session)
    # 3 PENDING (client à tester)
    for i in range(3):
        task_info = TaskInfo(
            task_id=f"test_task{i}",
            client_id="client",
            service="svc",
            status=TaskStatus.PENDING,
            request={},
            callback=None,
        )
        await repo.create_task_record(task_info)
    # 4 PENDING (un autre client)
    for i in range(3):
        task_info = TaskInfo(
            task_id=f"other_test_task{i}",
            client_id="other_client",
            service="svc",
            status=TaskStatus.PENDING,
            request={},
            callback=None,
        )
        await repo.create_task_record(task_info)
    # 1 RUNNING
    task_running = TaskInfo(
        task_id="test_task_running",
        client_id="client",
        service="svc",
        status=TaskStatus.IN_PROGRESS,
        request={},
        callback=None,
    )
    await repo.create_task_record(task_running)
    # 1 Another service
    task_other = TaskInfo(
        task_id="client_other_svc",
        client_id="client",
        service="task_other",
        status=TaskStatus.IN_PROGRESS,
        request={},
        callback=None,
    )
    await repo.create_task_record(task_other)

    nbr = await repo.count_pending_tasks_for_service_and_client("svc", "client")
    assert nbr == 3
