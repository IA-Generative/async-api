import json
from typing import Any

import yaml

from api.core.logger import logger


class ServicesConfig:
    def __init__(
        self,
        name: str,
        quotas: int | None = None,
        json_schema: dict[str, Any] | None = None,
        in_queue: str | None = None,
        out_queue: str | None = None,
    ) -> None:
        self.name = name
        self.quotas = quotas
        self.json_schema = json_schema
        self.in_queue = in_queue or f"{name}_in_queue"
        self.out_queue = out_queue or f"{name}_out_queue"

    def __repr__(self) -> str:
        return f"ServicesConfig(name={self.name}, quotas={self.quotas}, json_schema={self.json_schema}, in_queue={self.in_queue}, out_queue={self.out_queue})"  # noqa: E501


class ServicesConfigException(Exception):
    """Custom exception for ServicesConfigRepository errors."""


class ServicesConfigRepository:
    # Singleton instance to hold the services configuration
    SERVICES: dict = dict[str, ServicesConfig]()

    @staticmethod
    def load_services_config(svc_file: str) -> None:
        try:
            with open(svc_file) as file:  # noqa: PTH123
                config = yaml.load(file, Loader=yaml.SafeLoader)
                ServicesConfigRepository.SERVICES = ServicesConfigRepository._parse_yaml_struct(config)
        except FileNotFoundError as e:
            logger.error(f"Configuration file {svc_file} not found: {e}")
            msg = f"Configuration file {svc_file} not found."
            raise ServicesConfigException(msg) from e
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {svc_file}: {e}")
            msg = f"Error parsing YAML file {svc_file}."
            raise ServicesConfigException(msg) from e

    @staticmethod
    def _parse_yaml_struct(config: list[dict]) -> dict[str, ServicesConfig]:
        """Parses the YAML structure and returns a dictionary with service names as keys
        and their configurations as values.
        """
        if not isinstance(config, list):
            raise ServicesConfigException(
                "Invalid configuration format. Expected a list of services.",
            )

        services = {}
        for config_item in config:
            if not isinstance(config_item, dict):
                raise ServicesConfigException(
                    f"Invalid configuration item at: {config_item}. Expected a dictionary.",
                )
            if "name" not in config_item:
                raise ServicesConfigException(
                    "Each service configuration must contain a 'name' key.",
                )
            service_name = config_item["name"]
            service_quotas = config_item.get("quotas", None)
            json_schema = ServicesConfigRepository._handle_json_schema(
                config_item.get("json_schema", None),
            )

            in_queue = config_item.get("in_queue", f"{service_name}_in_queue")
            out_queue = config_item.get("out_queue", f"{service_name}_out_queue")
            service_config = ServicesConfig(
                name=service_name,
                quotas=service_quotas,
                json_schema=json_schema,
                in_queue=in_queue,
                out_queue=out_queue,
            )
            services[service_name] = service_config
        return services

    @staticmethod
    def _handle_json_schema(json_schema: str | None) -> dict[str, Any] | None:
        """
        Handles the JSON schema file path and returns its content.
        """
        if json_schema is not None:
            try:
                with open(json_schema) as file:  # noqa: PTH123
                    return json.load(file)
            except FileNotFoundError as e:
                raise ServicesConfigException(
                    f"JSON schema file {json_schema} not found.",
                ) from e
            except json.JSONDecodeError as e:
                raise ServicesConfigException(
                    f"Error parsing JSON schema file {json_schema}: {e}",
                ) from e
        return None

    def __init__(self) -> None:
        pass

    def all_services(self) -> dict[str, ServicesConfig]:
        """Returns all services configurations."""
        if not ServicesConfigRepository.SERVICES:
            raise ServicesConfigException(
                "No services loaded. Please load the services configuration first.",
            )
        return ServicesConfigRepository.SERVICES
