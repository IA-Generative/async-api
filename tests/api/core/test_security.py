from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from fastapi.security import HTTPBasicCredentials

from api.core.security import auth_guard
from api.schemas.errors import Unauthorized

if TYPE_CHECKING:
    from api.services.client_service import ClientService


@pytest.mark.asyncio
async def test_auth_guard_ok() -> None:
    client_service: ClientService = AsyncMock()
    client_service.is_valid_client_id.return_value = True

    client = await auth_guard(HTTPBasicCredentials(username="toto", password="password"), client_service)
    assert client == "toto"


@pytest.mark.asyncio
async def test_auth_guard_ko() -> None:
    client_service: ClientService = AsyncMock()
    client_service.is_valid_client_id.return_value = False

    with pytest.raises(Unauthorized):
        await auth_guard(HTTPBasicCredentials(username="toto", password="password"), client_service)
