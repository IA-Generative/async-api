from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends

from api.repositories.usage_repository import UsageRepository
from api.schemas.enum import TaskStatus
from api.schemas.usage import ClientUsageResponse, ServiceUsage


@dataclass
class _UsageCounts:
    success_count: int = 0
    failure_count: int = 0


class UsageService:
    def __init__(
        self,
        usage_repository: Annotated[UsageRepository, Depends(UsageRepository)],
    ) -> None:
        self.usage_repository = usage_repository

    async def get_client_usage(
        self,
        client_id: str,
        days: int = 30,
    ) -> ClientUsageResponse:
        since = datetime.now() - timedelta(days=days)
        rows = await self.usage_repository.count_usage_by_client(
            client_id=client_id,
            since=since,
        )

        usage_map: defaultdict[str, _UsageCounts] = defaultdict(_UsageCounts)
        for row in rows:
            if row.status == TaskStatus.SUCCESS:
                usage_map[row.service].success_count = row.count
            elif row.status == TaskStatus.FAILURE:
                usage_map[row.service].failure_count = row.count

        services = [
            ServiceUsage(
                service=svc,
                success_count=counts.success_count,
                failure_count=counts.failure_count,
            )
            for svc, counts in sorted(usage_map.items())
        ]

        return ClientUsageResponse(
            client_id=client_id,
            period_days=days,
            services=services,
        )
