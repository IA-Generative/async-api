"""Documentation du service `generation-render`."""

from pathlib import Path

TAG = "Remplissage de templates"

SHORT_DESCRIPTION = (
    "Remplit un template `.odt` avec un dictionnaire de données (publipostage programmatique, basé sur Relatorio)."
)

DESCRIPTION = (Path(__file__).parent / "content" / "generation_render.md").read_text(encoding="utf-8")
