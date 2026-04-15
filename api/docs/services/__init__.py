"""Documentation par service pour ReDoc.

Chaque service expose :
- `TAG` : nom du tag OpenAPI (affiché comme section dans ReDoc)
- `SHORT_DESCRIPTION` : phrase courte (utilisée dans la page catalogue)
- `DESCRIPTION` : description markdown complète (inputs, outputs, exemples)

Pour ajouter un nouveau service :
1. Créer un fichier `<service_name>.py` dans ce dossier
2. Définir `TAG`, `SHORT_DESCRIPTION` et `DESCRIPTION`
3. L'importer dans `SERVICE_DOCS` ci-dessous
"""

import re

from api.docs.services import generation_render

SERVICE_DOCS = [
    generation_render,
]

CATALOG_TAG = "Catalogue des services"


def _redoc_anchor(tag: str) -> str:
    """Transforme un nom de tag en ancre ReDoc.

    ReDoc génère des ancres au format `#tag/<slug>` où le slug remplace les
    caractères non-alphanumériques par des tirets.
    """
    slug = re.sub(r"[^\w]+", "-", tag).strip("-")
    return f"#tag/{slug}"


def _build_catalog_description() -> str:
    """Construit la page catalogue listant tous les services avec liens."""
    lines = [
        "Liste des services exposés par l'API. Chaque service a sa propre page de "
        "documentation avec son contrat d'interface (body, result), ses exemples et "
        "ses limites.\n",
        "| Service | Description | Documentation |",
        "|---|---|---|",
    ]
    for mod in SERVICE_DOCS:
        short = getattr(mod, "SHORT_DESCRIPTION", "—")
        anchor = _redoc_anchor(mod.TAG)
        lines.append(f"| `{mod.TAG}` | {short} | [Voir la doc]({anchor}) |")
    lines.append("")
    lines.append(
        "> Tous ces services sont consommables via la route générique "
        "`POST /v1/services/{service}/tasks` (voir section **Tasks**). "
        "Le nom du service à utiliser dans le path est indiqué dans la doc de chaque service.",
    )
    return "\n".join(lines)


def build_openapi_tags() -> list[dict]:
    """Retourne les tags OpenAPI à ajouter pour tous les services documentés.

    Le premier tag est la page catalogue (liste + liens), les suivants sont
    les pages détaillées de chaque service.
    """
    tags = [{"name": CATALOG_TAG, "description": _build_catalog_description()}]
    tags.extend(
        {"name": mod.TAG, "description": mod.DESCRIPTION}
        for mod in SERVICE_DOCS
    )
    return tags


def service_tag_names() -> list[str]:
    """Retourne la liste des noms de tags de services (pour x-tagGroups).

    Inclut la page catalogue en premier.
    """
    return [CATALOG_TAG, *(mod.TAG for mod in SERVICE_DOCS)]


def catalog_anchor() -> str:
    """Retourne l'ancre markdown vers la page catalogue (utilisée dans les autres tags)."""
    return _redoc_anchor(CATALOG_TAG)
