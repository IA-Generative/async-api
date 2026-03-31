from typing import Annotated

from fastapi import Depends

from api.models.client import Client, ClientServiceAuthorization
from api.repositories.client_repository import ClientRepository
from api.schemas.client import ClientCreateRequest, ClientResponse, ClientUpdateRequest
from api.schemas.errors import ClientAlreadyExists, ClientNotFound


class ClientService:
    """Service for managing client configurations and authorizations."""

    def __init__(
        self,
        client_repository: Annotated[ClientRepository, Depends(ClientRepository)],
    ) -> None:
        self.client_repository: ClientRepository = client_repository

    async def is_valid_client_id(self, client_id: str, client_secret: str | None) -> bool:
        """Check if the provided client ID is valid.
        Returns True if the client ID exists and is active, False otherwise.
        """
        client = await self.client_repository.get_active_client_by_client_id(client_id)
        if client is None:
            return False

        if client.client_secret is not None:
            return client.client_secret == client_secret

        return True

    async def get_client_authorization_for_service(
        self,
        client_id: str,
        service: str,
    ) -> ClientServiceAuthorization | None:
        """Check if a client is allowed to use a specific service.
        Returns ClientServiceAuthorization if the client is allowed, None otherwise.
        """
        client = await self.client_repository.get_active_client_by_client_id(client_id)
        if not client:
            return None

        for auth in client.authorizations:
            if auth.service in ("all", service):
                return auth

        return None

    async def create_client(self, body: ClientCreateRequest) -> ClientResponse:
        if await self.client_repository.client_id_exists(body.client_id):
            raise ClientAlreadyExists(details=f"Client '{body.client_id}' already exists.")

        client = Client(
            client_id=body.client_id,
            name=body.name,
            client_secret=body.client_secret,
            is_active=body.is_active,
            authorizations=[
                ClientServiceAuthorization(service=auth.service, quotas=auth.quotas) for auth in body.authorizations
            ],
        )
        client = await self.client_repository.create_client(client)
        return self._to_response(client)

    async def list_clients(self) -> list[ClientResponse]:
        clients = await self.client_repository.get_all_clients()
        return [self._to_response(c) for c in clients]

    async def get_client(self, client_id: str) -> ClientResponse:
        client = await self.client_repository.get_client_by_client_id(client_id)
        if not client:
            raise ClientNotFound(details=f"Client '{client_id}' not found.")
        return self._to_response(client)

    async def update_client(self, client_id: str, body: ClientUpdateRequest) -> ClientResponse:
        client = await self.client_repository.get_client_by_client_id(client_id)
        if not client:
            raise ClientNotFound(details=f"Client '{client_id}' not found.")

        if body.client_secret is not None:
            client.client_secret = body.client_secret

        if body.is_active is not None:
            client.is_active = body.is_active

        if body.authorizations is not None:
            client.authorizations = [
                ClientServiceAuthorization(service=auth.service, quotas=auth.quotas) for auth in body.authorizations
            ]

        client = await self.client_repository.update_client(client)
        return self._to_response(client)

    @staticmethod
    def _to_response(client: Client) -> ClientResponse:
        return ClientResponse(
            client_id=client.client_id,
            name=client.name,
            is_active=client.is_active,
            created_at=client.created_at,
            updated_at=client.updated_at,
            authorizations=[
                {"service": auth.service, "quotas": auth.quotas} for auth in client.authorizations
            ],
        )
