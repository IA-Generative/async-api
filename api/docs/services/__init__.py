"""Documentation par service pour ReDoc.

Les pages de documentation sont des fichiers markdown dans `content/`. Les liens
entre pages (catalogue, feuille de route, page de chaque service) sont injectés
au chargement via des placeholders résolus automatiquement :

- `{catalog_anchor}` — page catalogue
- `{roadmap_anchor}` — page feuille de route
- `{<service_name>_anchor}` — page d'un service déclaré dans `SERVICES`

Pour ajouter un service :
1. Créer `content/<name>.md` avec sa documentation
2. Ajouter une entrée `ServiceDoc(...)` dans `SERVICES`
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

CONTENT_DIR = Path(__file__).parent / "content"
CATALOG_TAG = "Catalogue des services"
ROADMAP_TAG = "Feuille de route"

# Tout placeholder de la forme `{<nom>_anchor}` non substitué indique une ancre
# cassée : on lève plutôt que de laisser un placeholder visible dans la doc.
_UNRESOLVED_ANCHOR_RE = re.compile(r"\{(\w+_anchor)\}")
_TAG_SLUG_RE = re.compile(r"[^\w]+")


@dataclass(frozen=True)
class ServiceDoc:
    """Métadonnées d'un service exposé dans la doc OpenAPI / ReDoc.

    `name` sert à la fois de nom de fichier markdown (`content/<name>.md`)
    et de clé pour le placeholder d'ancre (`{<name>_anchor}`).
    """

    name: str
    tag: str
    short_description: str

    @property
    def anchor(self) -> str:
        return _redoc_anchor(self.tag)

    @property
    def markdown_filename(self) -> str:
        return f"{self.name}.md"


SERVICES: tuple[ServiceDoc, ...] = (
    ServiceDoc(
        name="generation_render",
        tag="Remplissage de templates",
        short_description=(
            "Remplit un template `.odt` (Relatorio) ou `.docx` (Jinja2) "
            "avec un dictionnaire de données (publipostage programmatique)."
        ),
    ),
)


class _OpenApiTag(TypedDict):
    name: str
    description: str


def _redoc_anchor(tag: str) -> str:
    """Convertit un nom de tag en ancre ReDoc.

    ReDoc génère des ancres `#tag/<slug>` où le slug remplace tout caractère
    non-alphanumérique par un tiret.
    """
    return f"#tag/{_TAG_SLUG_RE.sub('-', tag).strip('-')}"


def _anchor_substitutions() -> dict[str, str]:
    """Mapping placeholder → URL pour toutes les ancres connues."""
    return {
        "catalog_anchor": _redoc_anchor(CATALOG_TAG),
        "roadmap_anchor": _redoc_anchor(ROADMAP_TAG),
        **{f"{svc.name}_anchor": svc.anchor for svc in SERVICES},
    }


def _render_markdown(filename: str, **extras: str) -> str:
    """Charge `content/<filename>` et substitue ses placeholders.

    Substitue tous les placeholders d'ancre déclarés (`{*_anchor}`) plus les
    `extras` éventuels (fragments contextuels comme un tableau dynamique).
    Lève si un placeholder `{*_anchor}` reste non résolu, pour éviter qu'un
    lien cassé ne se retrouve silencieusement dans la doc publiée.
    """
    text = (CONTENT_DIR / filename).read_text(encoding="utf-8")
    for placeholder, value in {**_anchor_substitutions(), **extras}.items():
        text = text.replace(f"{{{placeholder}}}", value)
    unresolved = sorted(set(_UNRESOLVED_ANCHOR_RE.findall(text)))
    if unresolved:
        raise RuntimeError(f"{filename}: placeholders d'ancre non résolus : {unresolved}")
    return text


def _services_table() -> str:
    """Tableau markdown listant tous les services (utilisé dans la page catalogue)."""
    return "\n".join(
        [
            "| Service | Description | Documentation |",
            "|---|---|---|",
            *(f"| `{svc.tag}` | {svc.short_description} | [Voir la doc]({svc.anchor}) |" for svc in SERVICES),
        ],
    )


def build_openapi_tags() -> list[_OpenApiTag]:
    """Tags OpenAPI : catalogue, feuille de route, puis une page par service."""
    return [
        {
            "name": CATALOG_TAG,
            "description": _render_markdown("catalog.md", services_table=_services_table()),
        },
        {
            "name": ROADMAP_TAG,
            "description": _render_markdown("roadmap.md"),
        },
        *({"name": svc.tag, "description": _render_markdown(svc.markdown_filename)} for svc in SERVICES),
    ]


def service_tag_names() -> list[str]:
    """Tags du groupe services (catalogue + une entrée par service)."""
    return [CATALOG_TAG, *(svc.tag for svc in SERVICES)]


def roadmap_tag_names() -> list[str]:
    """Tags du groupe feuille de route (exposé séparément dans ReDoc)."""
    return [ROADMAP_TAG]


def catalog_anchor() -> str:
    """Ancre markdown vers la page catalogue."""
    return _redoc_anchor(CATALOG_TAG)


def roadmap_anchor() -> str:
    """Ancre markdown vers la page feuille de route."""
    return _redoc_anchor(ROADMAP_TAG)
