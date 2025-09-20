from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from api.models.task import Task
from api.repositories.client_config_repository import ClientAuthorization
from api.schemas.enum import TaskStatus
from api.schemas.errors import BodyValidationError, Forbidden, ServiceNotFound, TooManyClientsRequests, TooManyRequests
from api.schemas.service import ServiceInfo
from api.schemas.task import TaskInfo, TaskRequest
from api.services.task_service import TaskService

if TYPE_CHECKING:
    from api.repositories.task_repository import TaskRepository
    from api.services.client_service import ClientService
    from api.services.queue_service import QueueSender
    from api.services.service_service import ServiceService


@pytest.fixture
def task_service() -> TaskService:
    task_repository_mock: TaskRepository = Mock()
    service_service_mock: ServiceService = Mock()
    client_service_mock: ClientService = Mock()
    queue_sender_mock: QueueSender = Mock()

    # ----------
    # SERVICE-SERVICE
    def get_service(service_name: str) -> ServiceInfo | None:
        if service_name == "svc_no_schema":
            return ServiceInfo(
                name="svc_no_schema",
                in_queue="in_queue",
                out_queue="out_queue",
            )
        if service_name == "svc_schema":
            return ServiceInfo(
                name="svc_no_schema",
                in_queue="in_queue",
                out_queue="out_queue",
                json_schema={
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {
                        "sleep": {"type": "integer", "description": "Durée d'attente en secondes"},
                        "mustSucceed": {"type": "boolean", "description": "Indique si la tâche doit réussir"},
                    },
                    "required": ["sleep"],
                    "additionalProperties": False,
                },
            )
        if service_name == "svc_quota_10":
            return ServiceInfo(
                name="svc_quota_10",
                in_queue="in_queue",
                out_queue="out_queue",
                quotas=10,
            )
        return None

    service_service_mock.get_service.side_effect = get_service

    # ----------
    # CLIENT-SERVICE
    def get_client_authorization_for_service(client_id: str, service: str) -> ClientAuthorization | None:
        if client_id == "client_with_auth_and_no_quota":
            return ClientAuthorization(service=service, quotas=None)
        if client_id == "client_with_auth_and_quota_10":
            return ClientAuthorization(service=service, quotas=10)
        return None

    client_service_mock.get_client_authorization_for_service.side_effect = get_client_authorization_for_service

    # ----------
    # TASK-REPO
    async def get_task_by_id(task_id: str, service: str) -> Task | None:  # noqa: ARG001
        if task_id == "valid_task":
            return Task(status=TaskStatus.IN_PROGRESS, task_id="69", response=None)
        return None

    async def get_task_position_by_id(task_id: str, service: str) -> int | None:  # noqa: ARG001
        return 42

    task_repository_mock.get_task_by_id.side_effect = get_task_by_id
    task_repository_mock.get_task_position_by_id.side_effect = get_task_position_by_id

    async def create_task_record(task_data_create: TaskInfo) -> Task:
        return Task(task_id=task_data_create.task_id)

    task_repository_mock.create_task_record = create_task_record

    # ----------
    # Queue sender
    async def send_task_to_queue(queue, task_data, service) -> None:  # noqa: ANN001
        pass

    queue_sender_mock.send_task_to_queue = send_task_to_queue

    return TaskService(
        task_repository=task_repository_mock,
        service_service=service_service_mock,
        client_service=client_service_mock,
        queue_sender=queue_sender_mock,
    )


def test_check_service_schema_with_no_schema(task_service: TaskService) -> None:
    task_service.check_service_schema("svc_no_schema", {})


def test_check_service_schema_with_schema_ok(task_service: TaskService) -> None:
    task_service.check_service_schema("svc_schema", {"sleep": 12})


def test_check_service_schema_with_schema_ko(task_service: TaskService) -> None:
    with pytest.raises(BodyValidationError):
        task_service.check_service_schema("svc_schema", {"bob": "leponge"})


@pytest.mark.asyncio
async def test_pool_task_with_invalid_service(task_service: TaskService) -> None:
    with pytest.raises(ServiceNotFound):
        await task_service.poll_task("task", "invalid_svc", "bob")


@pytest.mark.asyncio
async def test_pool_task_with_invalid_client_authorization(task_service: TaskService) -> None:
    with pytest.raises(Forbidden):
        await task_service.poll_task("task", "svc_no_schema", "bob")


@pytest.mark.asyncio
async def test_pool_task_not_found(task_service: TaskService) -> None:
    task = await task_service.poll_task("invalid_task", "svc_no_schema", "client_with_auth_and_no_quota")
    assert task is None


@pytest.mark.asyncio
async def test_pool_task_ok(task_service: TaskService) -> None:
    task = await task_service.poll_task("valid_task", "svc_no_schema", "client_with_auth_and_no_quota")
    assert task is not None
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.task_id == "69"


@pytest.mark.asyncio
async def test_submit_task_with_invalid_service(task_service: TaskService) -> None:
    task = TaskRequest(body={}, callback=None)
    with pytest.raises(ServiceNotFound):
        await task_service.submit_task(task, "invalid_svc", "bob")


@pytest.mark.asyncio
async def test_submit_task_with_invalid_client_authorization(task_service: TaskService) -> None:
    task = TaskRequest(body={}, callback=None)
    with pytest.raises(Forbidden):
        await task_service.submit_task(task, "svc_no_schema", "bob")


@pytest.mark.asyncio
async def test_submit_task_with_service_quota_ko(task_service: TaskService) -> None:
    task = TaskRequest(body={}, callback=None)

    async def count_pending_tasks_for_service(service) -> int:  # noqa: ARG001, ANN001
        return 10

    task_service.task_repository.count_pending_tasks_for_service = count_pending_tasks_for_service

    with pytest.raises(TooManyRequests):
        await task_service.submit_task(task, "svc_quota_10", "client_with_auth_and_no_quota")


@pytest.mark.asyncio
async def test_submit_task_with_user_quota_ko(task_service: TaskService) -> None:
    task = TaskRequest(body={}, callback=None)

    async def count_pending_tasks_for_service(service) -> int:  # noqa: ARG001, ANN001
        return 9

    task_service.task_repository.count_pending_tasks_for_service = count_pending_tasks_for_service

    async def count_pending_tasks_for_service_and_client(service, client_id: str) -> int:  # noqa: ARG001, ANN001
        return 11

    task_service.task_repository.count_pending_tasks_for_service_and_client = count_pending_tasks_for_service_and_client

    with pytest.raises(TooManyClientsRequests):
        await task_service.submit_task(task, "svc_quota_10", "client_with_auth_and_quota_10")


@pytest.mark.asyncio
async def test_submit_task_with_user_quota_ok(task_service: TaskService) -> None:
    task = TaskRequest(body={}, callback=None)

    async def count_pending_tasks_for_service(service) -> int:  # noqa: ARG001, ANN001
        return 9

    task_service.task_repository.count_pending_tasks_for_service = count_pending_tasks_for_service

    async def count_pending_tasks_for_service_and_client(service, client_id: str) -> int:  # noqa: ARG001, ANN001
        return 9

    task_service.task_repository.count_pending_tasks_for_service_and_client = count_pending_tasks_for_service_and_client

    task_data = await task_service.submit_task(task, "svc_quota_10", "client_with_auth_and_quota_10")
    assert task_data.task_position == 42
