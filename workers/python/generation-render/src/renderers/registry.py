from src.renderers.base import TemplateRenderer
from src.renderers.docx import DocxRenderer
from src.renderers.odt import OdtRenderer

RENDERERS: dict[str, type[TemplateRenderer]] = {
    ".odt": OdtRenderer,
    ".docx": DocxRenderer,
}


def get_renderer(file_id: str) -> TemplateRenderer:
    """Return the appropriate renderer based on the file extension.

    Raises:
        ValueError: if no renderer supports the file extension.
    """
    for ext, renderer_cls in RENDERERS.items():
        if file_id.endswith(ext):
            return renderer_cls()

    supported = ", ".join(RENDERERS.keys())
    msg = f"Unsupported file format for '{file_id}'. Supported: {supported}"
    raise ValueError(msg)
