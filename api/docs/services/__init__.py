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

    Présente l'ordre de mise à disposition des services — disponibles et à venir —
    avec une description courte de chacun.
    """
    generation_render_anchor = _redoc_anchor(generation_render.TAG)
    return f"""
Ordre de mise à disposition progressive des services sur AsyncTaskAPI. Les services
sont déployés au fil des validations fonctionnelles et techniques.

## Vue d'ensemble

| # | Service | Identifiant API | Statut |
|---|---|---|---|
| 1 | Remplissage de template | `generation-render` | ✅ **Disponible** |
| 2 | Extraction de texte | `extract-text` | 🚧 À venir |
| 3 | Classification de documents | _à définir_ | 🚧 À venir |
| 4 | Extraction de données (entités nommées) | _à définir_ | 🚧 À venir |

---

## 1. ✅ Remplissage de template

**Statut : disponible en production.** **Identifiant API :** `generation-render`

Remplit un template `.odt` (format OpenDocument) à partir d'un dictionnaire de données,
via un moteur de publipostage programmatique (Relatorio / Genshi). Gère les placeholders
simples, les conditionnelles (`if`) et les boucles (`for`). Utile pour la génération
automatisée de courriers, convocations, attestations, etc.

→ [Voir la documentation complète]({generation_render_anchor})

---

## 2. 🚧 Extraction de texte

**Statut : à venir.** **Identifiant API :** `extract-text`

Extrait le texte brut depuis des documents numériques ou scannés. Prend en charge les PDF
(natifs comme scannés), les images (PNG, JPEG, TIFF, …) et s'appuie sur un pipeline OCR
pour les contenus non textuels.

Service fondamental : il alimente les traitements en aval (classification, extraction
d'entités). Un document scanné devient exploitable dès que son contenu textuel est
récupérable.

---

## 3. 🚧 Classification de documents

**Statut : à venir.**

Identifie automatiquement le type d'un document à partir de son contenu textuel (issu
par exemple du service `extract-text`). Permet de router un document vers le processus
métier adapté : pièce d'identité, jugement, formulaire administratif, courrier, etc.

Typiquement utilisé en amont d'une extraction d'entités pour appliquer le bon modèle
selon la catégorie détectée.

---

## 4. 🚧 Extraction de données (entités nommées)

**Statut : à venir.**

Extrait les entités nommées structurées présentes dans un texte : personnes, dates,
adresses, numéros de dossier, montants, identifiants, etc. Transforme un document brut
en données exploitables par les systèmes métier.

Conçu pour s'articuler avec les services amont (`extract-text` + classification) afin
de couvrir l'ensemble de la chaîne : document brut → texte → type → données structurées.

---

## Légende

- ✅ **Disponible** — service en production, consommable via `POST /v1/services/{{service}}/tasks`
- 🚧 **À venir** — service planifié, contrat d'API en cours de définition

> Pour toute demande d'accès anticipé ou de cadrage, contacter l'équipe BRIO.
"""


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
