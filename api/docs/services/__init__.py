"""Documentation par service pour ReDoc.

Chaque service expose :
- `TAG` : nom du tag OpenAPI (affiché comme section dans ReDoc)
- `SHORT_DESCRIPTION` : phrase courte (utilisée dans la page catalogue)
- `DESCRIPTION` : description markdown complète (inputs, outputs, exemples),
  généralement chargée depuis `content/<service_name>.md`

Pour ajouter un nouveau service :
1. Créer un fichier `content/<service_name>.md` avec la description markdown
2. Créer un fichier `<service_name>.py` dans ce dossier qui définit
   `TAG`, `SHORT_DESCRIPTION` et `DESCRIPTION` (chargé depuis le .md)
3. L'importer dans `SERVICE_DOCS` ci-dessous
"""

import re
from pathlib import Path

from api.docs.services import generation_render

CONTENT_DIR = Path(__file__).parent / "content"

SERVICE_DOCS = [
    generation_render,
]

CATALOG_TAG = "Catalogue des services"
ROADMAP_TAG = "Feuille de route"


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
    lines.append("")
    lines.append(
        f"Pour voir l'ordre de mise à disposition des prochains services, consultez la "
        f"[**Feuille de route**]({_redoc_anchor(ROADMAP_TAG)}).",
    )
    return "\n".join(lines)


def _build_roadmap_description() -> str:
    """Construit la page de feuille de route des services.

    Charge le markdown depuis `content/roadmap.md` et y injecte les ancres
    dynamiques vers les pages de services.
    """
    template = (CONTENT_DIR / "roadmap.md").read_text(encoding="utf-8")
    return template.replace(
        "{generation_render_anchor}",
        _redoc_anchor(generation_render.TAG),
    )


def build_openapi_tags() -> list[dict]:
    """Retourne les tags OpenAPI à ajouter pour tous les services documentés.

    Ordre : catalogue → feuille de route → pages détaillées par service.
    """
    tags = [
        {"name": CATALOG_TAG, "description": _build_catalog_description()},
        {"name": ROADMAP_TAG, "description": _build_roadmap_description()},
    ]
    tags.extend({"name": mod.TAG, "description": mod.DESCRIPTION} for mod in SERVICE_DOCS)
    return tags


def service_tag_names() -> list[str]:
    """Retourne la liste des noms de tags de services (pour x-tagGroups).

    Inclut la page catalogue en premier, puis les pages détaillées par service.
    La feuille de route est exposée séparément via `roadmap_tag_names()` pour
    constituer son propre groupe dans ReDoc.
    """
    return [CATALOG_TAG, *(mod.TAG for mod in SERVICE_DOCS)]


def roadmap_tag_names() -> list[str]:
    """Retourne la liste des tags du groupe feuille de route (pour x-tagGroups)."""
    return [ROADMAP_TAG]


def catalog_anchor() -> str:
    """Retourne l'ancre markdown vers la page catalogue (utilisée dans les autres tags)."""
    return _redoc_anchor(CATALOG_TAG)


def roadmap_anchor() -> str:
    """Retourne l'ancre markdown vers la page feuille de route."""
    return _redoc_anchor(ROADMAP_TAG)
