from .callback import TaskCallback
from .queue import QueueData, QueueTask
from .service import ServiceInfo
from .status import HealthResponse, ReadyComponent, ReadyResponse
from .storage import StorageUploadResponse
from .task import (
    Callback,
    TaskDataFailed,
    TaskDataPending,
    TaskDataProgress,
    TaskDataSuccess,
    TaskErrorResponse,
    TaskInfo,
    TaskRequest,
    TaskResponse,
)
from .usage import ClientUsageResponse, ServiceUsage

_callback_schemas = [
    "TaskCallback",
]

_queue_schemas = [
    "QueueData",
    "QueueTask",
]

_service_schemas = [
    "ServiceInfo",
]

_status_schemas = [
    "HealthResponse",
    "ReadyComponent",
    "ReadyResponse",
]

_storage_schemas = [
    "StorageUploadResponse",
]

_task_schemas = [
    "Callback",
    "TaskDataFailed",
    "TaskDataPending",
    "TaskDataProgress",
    "TaskDataSuccess",
    "TaskErrorResponse",
    "TaskInfo",
    "TaskRequest",
    "TaskResponse",
]

# usage
_usage_schemas = [
    "ClientUsageResponse",
    "ServiceUsage",
]

__all__ = [
    *_callback_schemas,
    *_queue_schemas,
    *_service_schemas,
    *_status_schemas,
    *_storage_schemas,
    *_task_schemas,
    *_usage_schemas,
]
