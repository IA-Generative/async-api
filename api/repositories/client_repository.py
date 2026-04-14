from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.models.client import Client


class ClientRepository:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db_session)]) -> None:
        self.db: AsyncSession = db

    async def get_active_client_by_client_id(self, client_id: str) -> Client | None:
        stmt = select(Client).where((Client.client_id == client_id) & (Client.is_active.is_(True)))
        result = await self.db.execute(statement=stmt)
        return result.scalar_one_or_none()

    async def get_client_by_client_id(self, client_id: str) -> Client | None:
        stmt = select(Client).where(Client.client_id == client_id)
        result = await self.db.execute(statement=stmt)
        return result.scalar_one_or_none()

    async def get_all_clients(self) -> list[Client]:
        stmt = select(Client).where(Client.is_active.is_(True))
        result = await self.db.execute(statement=stmt)
        return list(result.scalars().all())

    async def create_client(self, client: Client) -> Client:
        self.db.add(instance=client)
        await self.db.commit()
        await self.db.refresh(instance=client)
        return client

    async def update_client(self, client: Client) -> Client:
        await self.db.commit()
        await self.db.refresh(instance=client)
        return client

    async def delete_client_soft(self, client: Client) -> Client:
        client.is_active = False
        await self.db.commit()
        await self.db.refresh(instance=client)
        return client

    async def client_id_exists(self, client_id: str) -> bool:
        stmt = select(Client.id).where(Client.client_id == client_id)
        result = await self.db.execute(statement=stmt)
        return result.scalar_one_or_none() is not None
