from typing import Annotated

from fastapi import Depends

from api.repositories.client_config_repository import ClientAuthorization, ClientConfigRepository


class ClientService:
    """Service for managing client configurations and authorizations."""

    def __init__(
        self,
        client_config_repository: Annotated[ClientConfigRepository, Depends(ClientConfigRepository)],
    ) -> None:
        self.client_config_repository: ClientConfigRepository = client_config_repository

    def is_valid_client_id(self, client_id: str, client_secret: str | None) -> bool:
        """Check if the provided client ID is valid.
        Returns True if the client ID exists, False otherwise.
        """
        client_config = self.client_config_repository.get_client(client_id)
        # Client does not exist
        if client_config is None:
            return False

        # Client secret is required but not provided
        if client_config.client_secret is not None:
            return client_config.client_secret == client_secret

        return True

    def get_client_authorization_for_service(self, client_id: str, service: str) -> ClientAuthorization | None:
        """Check if a client is allowed to use a specific service.
        Returns ClientAuthorization if the client is allowed, None otherwise.
        """
        client_config = self.client_config_repository.get_client(client_id)
        if not client_config:
            return None

        # Check if the client has all authorization for the service
        authorization = client_config.authorizations.get("all")
        if authorization is not None:
            return authorization

        # Check if the client has authorization for the service spécified
        authorization = client_config.authorizations.get(service)
        if authorization is not None:
            return authorization

        return None
