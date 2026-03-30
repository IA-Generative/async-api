from fastapi import FastAPI

from api.core.config import settings
from api.core.exception_handlers import register_exception_handlers
from api.core.logger import logger
from api.core.utils import get_version
from api.repositories.client_config_repository import ClientConfigRepository
from api.repositories.services_config_repository import ServicesConfigRepository
from api.routes import metrics, services, status, storage, tasks

__version__, __name__ = get_version()

logger.info("🚀 Starting async API")
logger.info("⏳ Loading services configuration ...")
logger.info(f"Using services config file: {settings.SERVICES_CONFIG_FILE}")
ServicesConfigRepository.load_services_config(settings.SERVICES_CONFIG_FILE)
for service in ServicesConfigRepository.SERVICES:
    logger.info(f"- Service loaded: {service}")
logger.info("🤗 Done.")

logger.info("⏳ Loading clients configuration ...")
logger.info(f"Using clients config file: {settings.CLIENTS_CONFIG_FILE}")
ClientConfigRepository.load_clients_config(settings.CLIENTS_CONFIG_FILE)
for client in ClientConfigRepository.CLIENTS:
    logger.info(f"- client loaded: {client}")
logger.info("🤗 Done.")

logger.info("⏳ Registering API routes ...")
app = FastAPI(
    title=__name__,
    version=__version__,
    summary=settings.PROJECT_DESCRIPTION,
)
register_exception_handlers(app=app)

app.include_router(router=services.router, prefix="/v1", tags=["Services"])
app.include_router(router=tasks.router, prefix="/v1", tags=["Tasks"])
app.include_router(router=storage.router, prefix="/storage", tags=["Storage"])
app.include_router(router=metrics.router, prefix="/internal", tags=["Metrics"])
app.include_router(router=status.router, prefix="/internal", tags=["Status"])
logger.info("API routes registered successfully.")
