from enum import StrEnum
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from api.core.config import settings
from api.core.exception_handlers import register_exception_handlers
from api.core.logger import logger
from api.core.utils import get_version
from api.docs.services import build_openapi_tags, catalog_anchor, service_tag_names
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

# Tags techniques (routes) — utilisés par Swagger ET ReDoc
technical_tags = [
    {
        "name": "Tasks",
        "description": (
            "Création et suivi des tâches asynchrones via une route générique paramétrée par `service`. "
            "Le format du `body` et du `result` dépend du service ciblé — "
            f"voir le [**Catalogue des services**]({catalog_anchor()}) pour la liste et les contrats."
        ),
    },
    {
        "name": "Services",
        "description": (
            "Liste des services disponibles (endpoint dynamique). "
            f"Pour les contrats détaillés de chaque service, voir le "
            f"[**Catalogue des services**]({catalog_anchor()})."
        ),
    },
    {"name": "Storage", "description": "Upload de fichiers dans le stockage S3."},
    {"name": "Clients", "description": "Administration des clients et de leurs autorisations."},
    {"name": "Metrics", "description": "Métriques Prometheus exposées par l'API."},
    {"name": "Status", "description": "Endpoints internes de santé (health, ready)."},
    {"name": "Usage", "description": "Statistiques d'usage par client."},
]

# URL de l'OpenAPI spécifique à ReDoc (enrichi des tags documentaires)
REDOC_OPENAPI_URL = "/openapi-redoc.json"

app = FastAPI(
    title=__name__,
    version=__version__,
    summary=settings.PROJECT_DESCRIPTION,
    openapi_tags=technical_tags,
    # ReDoc utilisera son propre schema OpenAPI
    redoc_url=None,
)


@app.get("/redoc", include_in_schema=False)
def redoc_html() -> object:
    """Sert ReDoc en pointant vers l'OpenAPI enrichi."""
    return get_redoc_html(openapi_url=REDOC_OPENAPI_URL, title=f"{__name__} — Documentation")


@app.get(REDOC_OPENAPI_URL, include_in_schema=False)
def openapi_redoc() -> JSONResponse:
    """Schéma OpenAPI enrichi pour ReDoc.

    Ajoute les tags documentaires (catalogue + un tag par service) et les
    `x-tagGroups` pour regrouper visuellement dans ReDoc. Swagger continue
    d'utiliser le schéma de base (propre, focus testing).
    """
    base_schema = app.openapi()
    # Copie défensive pour ne pas muter le schema mis en cache par FastAPI
    schema = dict(base_schema)
    schema["tags"] = technical_tags + build_openapi_tags()
    schema["x-tagGroups"] = [
        {
            "name": "API",
            "tags": [tag["name"] for tag in technical_tags],
        },
        {
            "name": "Services disponibles",
            "tags": service_tag_names(),
        },
    ]
    return JSONResponse(schema)


register_exception_handlers(app=app)

app.include_router(router=services.router, prefix=RoutePrefix.V1)
app.include_router(router=tasks.router, prefix=RoutePrefix.V1)
app.include_router(router=storage.router, prefix=RoutePrefix.STORAGE)
app.include_router(router=clients.router, prefix=RoutePrefix.INTERNAL)
app.include_router(router=metrics.router, prefix=RoutePrefix.INTERNAL)
app.include_router(router=status.router, prefix=RoutePrefix.INTERNAL)
app.include_router(router=usage.router, prefix=RoutePrefix.INTERNAL)

# Serve documentation examples (templates, sample data) as static files.
# Accessible at /docs-examples/<service>/<filename>
_examples_dir = Path(__file__).parent / "docs" / "examples"
if _examples_dir.exists():
    app.mount(
        "/docs-examples",
        StaticFiles(directory=str(_examples_dir)),
        name="docs-examples",
    )

logger.info("API routes registered successfully.")
