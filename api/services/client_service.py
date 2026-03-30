from typing import Annotated

from fastapi import Depends

from api.models.client import ClientServiceAuthorization
from api.repositories.client_repository import ClientRepository


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
        client = await self.client_repository.get_client_by_client_id(client_id)
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
        client = await self.client_repository.get_client_by_client_id(client_id)
        if not client:
            return None

        for auth in client.authorizations:
            if auth.service == "all":
                return auth

        for auth in client.authorizations:
            if auth.service == service:
                return auth

        return None
