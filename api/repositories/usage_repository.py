from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.models.task import Task
from api.schemas.enum import TaskStatus


class UsageCountView:
    def __init__(self, service: str, status: str, count: int) -> None:
        self.service: str = service
        self.status: str = status
        self.count: int = count


class UsageRepository:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db_session)]) -> None:
        self.db: AsyncSession = db

    async def count_usage_by_client(
        self,
        client_id: str,
        since: datetime,
    ) -> list[UsageCountView]:
        statement = (
            select(Task.service, Task.status, func.count(Task.id).label("count"))
            .where(
                Task.client_id == client_id,
                Task.submition_date >= since,
                Task.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILURE]),
            )
            .group_by(Task.service, Task.status)
        )
        rows = await self.db.execute(statement=statement)
        return [UsageCountView(service=r[0], status=r[1], count=r[2]) for r in rows.all()]
