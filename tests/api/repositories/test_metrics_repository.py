import uuid

import pytest

from api.repositories.metrics_repository import MetricsTaskRepository
from api.repositories.task_repository import TaskRepository
from api.schemas.enum import TaskStatus
from api.schemas.task import TaskInfo


@pytest.mark.asyncio
async def test_count_tasks_per_status_and_service(async_db_session) -> None:  # noqa: ANN001
    dataset: dict[str, dict[str, int]] = {
        "svc1": {
            TaskStatus.PENDING: 5,
            TaskStatus.IN_PROGRESS: 4,
            TaskStatus.SUCCESS: 3,
            TaskStatus.FAILURE: 2,
        },
        "svc2": {
            TaskStatus.PENDING: 2,
            TaskStatus.IN_PROGRESS: 3,
            TaskStatus.SUCCESS: 4,
            TaskStatus.FAILURE: 5,
        },
    }
    await create_dataset(async_db_session, dataset)
    repo = MetricsTaskRepository(async_db_session)
    results = await repo.count_tasks_per_status_and_service()

    for result in results:
        expected_count = dataset[result.service][result.status]
        assert expected_count == result.count


@pytest.mark.asyncio
async def test_running_and_pending_tasks(async_db_session) -> None:  # noqa: ANN001
    dataset: dict[str, dict[str, int]] = {
        "svc1": {
            TaskStatus.PENDING: 5,
            TaskStatus.IN_PROGRESS: 4,
            TaskStatus.SUCCESS: 3,
            TaskStatus.FAILURE: 2,
        },
        "svc2": {
            TaskStatus.PENDING: 20,
            TaskStatus.IN_PROGRESS: 3,
            TaskStatus.SUCCESS: 4,
            TaskStatus.FAILURE: 5,
        },
    }
    await create_dataset(async_db_session, dataset)
    repo = MetricsTaskRepository(async_db_session)
    results = await repo.running_and_pending_tasks()
    assert (
        len(results)
        == dataset["svc1"][TaskStatus.PENDING]
        + dataset["svc1"][TaskStatus.IN_PROGRESS]
        + dataset["svc2"][TaskStatus.PENDING]
        + dataset["svc2"][TaskStatus.IN_PROGRESS]
    )


async def create_dataset(async_session, dataset) -> None:  # noqa: ANN001
    repo = TaskRepository(async_session)

    for svc_name, statuses in dataset.items():
        for status, count in statuses.items():
            for _i in range(count):
                task = TaskInfo(
                    task_id=str(uuid.uuid4()),
                    client_id="client",
                    service=svc_name,
                    status=status,
                    request={},
                    callback=None,
                )
                await repo.create_task_record(task)
