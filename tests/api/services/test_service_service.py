from unittest.mock import Mock

import pytest

from api.repositories.services_config_repository import ServicesConfig, ServicesConfigRepository
from api.services.service_service import ServiceService


@pytest.fixture
def services_config_repo_mock() -> ServicesConfigRepository:
    services_config_repo_mock: ServicesConfigRepository = Mock()  # type: ignore
    services_config_repo_mock.all_services.return_value = {
        "example": ServicesConfig(
            name="example",
            quotas=1000,
            json_schema={"$schema": "http://json-schema.org/draft-07/schema#"},
            in_queue="example_in_queue",
            out_queue="example_out_queue",
        ),
        "example2": ServicesConfig(
            name="example2",
            quotas=None,
            json_schema=None,
            in_queue="the_in_queue",
            out_queue="the_out_queue",
        ),
    }
    return services_config_repo_mock


def test_check_service_exists(services_config_repo_mock: ServicesConfigRepository) -> None:
    service_service = ServiceService(services_config_repo_mock)

    # Test with an existing service
    service_service.check_service_exists("example")

    # Test with a non-existing service
    with pytest.raises(Exception):  # noqa: PT011, B017
        service_service.check_service_exists("non_existing_service")


def test_list_services_names(services_config_repo_mock: ServicesConfigRepository) -> None:
    service_service = ServiceService(services_config_repo_mock)
    services = service_service.list_services_names()
    assert "example" in services
    assert "example2" in services


def test_list_all(services_config_repo_mock: ServicesConfigRepository) -> None:
    service_service = ServiceService(services_config_repo_mock)

    services = service_service.list_all()
    assert len(services) == 2
    example = next((i for i in services if i.name == "example"), None)
    example2 = next((i for i in services if i.name == "example2"), None)
    assert example is not None
    assert example2 is not None
    assert example.name == "example"
    assert example2.name == "example2"
    assert example.json_schema is not None
    assert example2.json_schema is None


def test_get_service_ok(services_config_repo_mock: ServicesConfigRepository) -> None:
    service_service = ServiceService(services_config_repo_mock)

    assert service_service.get_service("example") is not None


def test_get_service_ko(services_config_repo_mock: ServicesConfigRepository) -> None:
    service_service = ServiceService(services_config_repo_mock)

    assert service_service.get_service("example666") is None
