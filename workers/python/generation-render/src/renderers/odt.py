import re
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from loguru import logger
from relatorio.templates.opendocument import Template

from src.renderers.base import RenderResult, TemplateRenderer

PLACEHOLDER_PATTERN = re.compile(r"&lt;(\w+(?:\.\w+)?)&gt;")
FOR_VARIABLE_PATTERN = re.compile(
    r'for%20each=(?:&quot;|"|%22)(\w+)(?:%20|\s)in',
)


def _extract_placeholder_keys(odt_content: bytes) -> set[str]:
    """Extract placeholder names from the ODT content.xml.

    Excludes loop iteration variables (e.g. 'item' in 'for each="item in items"')
    and dotted access (e.g. 'mesure.department').
    """
    with zipfile.ZipFile(BytesIO(odt_content), "r") as z:
        xml = z.read("content.xml").decode("utf-8")
    all_keys = set(PLACEHOLDER_PATTERN.findall(xml))
    loop_vars = set(FOR_VARIABLE_PATTERN.findall(xml))
    return {k for k in all_keys if k not in loop_vars and "." not in k}


class OdtRenderer(TemplateRenderer):
    def render(self, template_content: bytes, data: dict[str, str]) -> RenderResult:
        expected_keys = _extract_placeholder_keys(template_content)
        provided_keys = set(data.keys())
        missing_keys = sorted(expected_keys - provided_keys)

        with tempfile.NamedTemporaryFile(suffix=".odt", delete=False) as tmp:
            tmp.write(template_content)
            tmp_path = Path(tmp.name)

        try:
            template = Template(source="", filepath=str(tmp_path), lookup="lenient")
            output = template.generate(**data).render()
            rendered_bytes: bytes = output.getvalue()
        finally:
            tmp_path.unlink(missing_ok=True)

        warnings = [
            f"La donnée pour '{key}' n'est pas définie"
            for key in missing_keys
        ]

        if warnings:
            logger.warning(f"Missing keys: {missing_keys}")

        return RenderResult(content=rendered_bytes, warnings=warnings)
