from enum import StrEnum

from fastapi import FastAPI

from api.core.config import settings
from api.core.exception_handlers import register_exception_handlers
from api.core.logger import logger
from api.core.utils import get_version
from api.repositories.services_config_repository import ServicesConfigRepository
from api.routes import clients, metrics, services, status, storage, tasks, usage

__version__, __name__ = get_version()


class RoutePrefix(StrEnum):
    V1 = "/v1"
    STORAGE = "/storage"
    INTERNAL = "/internal"

logger.info("🚀 Starting async API")
logger.info("⏳ Loading services configuration ...")
logger.info(f"Using services config file: {settings.SERVICES_CONFIG_FILE}")
ServicesConfigRepository.load_services_config(settings.SERVICES_CONFIG_FILE)
for service in ServicesConfigRepository.SERVICES:
    logger.info(f"- Service loaded: {service}")
logger.info("🤗 Done.")

logger.info("⏳ Registering API routes ...")
app = FastAPI(
    title=__name__,
    version=__version__,
    summary=settings.PROJECT_DESCRIPTION,
)
register_exception_handlers(app=app)

app.include_router(router=services.router, prefix=RoutePrefix.V1, tags=["Services"])
app.include_router(router=tasks.router, prefix=RoutePrefix.V1, tags=["Tasks"])
app.include_router(router=storage.router, prefix=RoutePrefix.STORAGE, tags=["Storage"])
app.include_router(router=clients.router, prefix=RoutePrefix.INTERNAL, tags=["Clients"])
app.include_router(router=metrics.router, prefix=RoutePrefix.INTERNAL, tags=["Metrics"])
app.include_router(router=status.router, prefix=RoutePrefix.INTERNAL, tags=["Status"])
app.include_router(router=usage.router, prefix=RoutePrefix.INTERNAL, tags=["Usage"])
logger.info("API routes registered successfully.")
