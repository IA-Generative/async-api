from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.models.task import Task
from api.schemas.enum import TaskStatus


class TaskCountByStatusAndServiceView:
    def __init__(self, service: str, status: str, client_id: str, count: int) -> None:
        self.service: str = service
        self.status: str = status
        self.client_id: str = client_id
        self.count: int = count

    def __repr__(self) -> str:
        return (
            f"TaskCountByStatusAndServiceView(service={self.service},"
            f"status={self.status}, client_id={self.client_id}, count={self.count})"
        )


class PendingAndRunningTaskView:
    def __init__(
        self, service: str, status: str, client_id: str, submition_date: datetime, start_date: datetime,
    ) -> None:
        self.service: str = service
        self.status: str = status
        self.client_id: str = client_id
        self.submition_date: datetime = submition_date
        self.start_date: datetime = start_date

    def __repr__(self) -> str:
        return (
            f"PendingAndRunningTaskView(service={self.service},"
            "status={self.status}, client_id={self.client_id},"
            "submition_date={self.submition_date},"
            "start_date={self.start_date})"
        )


class MetricsTaskRepository:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db_session)]) -> None:
        self.db: AsyncSession = db

    async def count_tasks_per_status_and_service(
        self,
    ) -> list[TaskCountByStatusAndServiceView]:
        """Get the count of tasks per status and service.

        Returns:
            list[TaskCountByStatusAndServiceView]: A list of task counts grouped by status and service.

        """
        statement = select(
            Task.service, Task.status, Task.client_id, func.count(Task.service).label("count"),
        ).group_by(
            Task.service,
            Task.status,
            Task.client_id,
        )
        rows = await self.db.execute(statement=statement)
        return [
            TaskCountByStatusAndServiceView(
                service=row.service, status=row.status, client_id=row.client_id, count=row.count,
            )
            for row in rows.all()
        ]

    async def running_and_pending_tasks(self) -> list[PendingAndRunningTaskView]:
        rows = await self.db.execute(
            statement=select(Task.service, Task.status, Task.client_id, Task.submition_date, Task.start_date).where(
                or_(Task.status == TaskStatus.PENDING, Task.status == TaskStatus.IN_PROGRESS),
            ),
        )
        return [
            PendingAndRunningTaskView(
                service=row.service,
                status=row.status,
                client_id=row.client_id,
                submition_date=row.submition_date,
                start_date=row.start_date,
            )
            for row in rows.all()
        ]
