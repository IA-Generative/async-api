from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from api.schemas.errors import Unauthorized
from api.services.client_service import ClientService

httpbasic = HTTPBasic()


async def auth_guard(
    credentials: Annotated[HTTPBasicCredentials, Depends(httpbasic)],
    client_service: Annotated[ClientService, Depends(ClientService)],
) -> str:
    if not await client_service.is_valid_client_id(client_id=credentials.username, client_secret=credentials.password):
        raise Unauthorized(details="Client is not authorized.")
    return credentials.username
