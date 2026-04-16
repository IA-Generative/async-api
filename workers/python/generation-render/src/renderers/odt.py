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
FOR_ITERABLE_PATTERN = re.compile(
    r'for%20each=(?:&quot;|"|%22)\w+(?:%20|\s)in(?:%20|\s)(\w+)',
)
IF_VARIABLE_PATTERN = re.compile(
    r'if%20test=(?:&quot;|"|%22)(\w+)',
)


def _extract_template_keys(odt_content: bytes) -> tuple[set[str], set[str]]:
    """Extract all variable names from the ODT content.xml.

    Returns:
        (placeholder_keys, all_keys):
        - placeholder_keys: simple <variable> placeholders (for warning on missing)
        - all_keys: all variables needed by Relatorio (placeholders + if/for variables)
    """
    with zipfile.ZipFile(BytesIO(odt_content), "r") as z:
        xml = z.read("content.xml").decode("utf-8")

    # Simple placeholders: <variable>
    all_placeholders = set(PLACEHOLDER_PATTERN.findall(xml))
    loop_vars = set(FOR_VARIABLE_PATTERN.findall(xml))
    placeholder_keys = {k for k in all_placeholders if k not in loop_vars and "." not in k}

    # Variables used in if-conditions
    if_vars = set(IF_VARIABLE_PATTERN.findall(xml))

    # Iterables used in for-loops
    for_iterables = set(FOR_ITERABLE_PATTERN.findall(xml))

    all_keys = placeholder_keys | if_vars | for_iterables

    return placeholder_keys, all_keys


def _normalize_value(value: object) -> str:
    """Normalize a value to string for Relatorio templates.
    """
    if isinstance(value, bool):
        return "true" if value else ""
    if isinstance(value, list):
        return value
    return str(value)


class OdtRenderer(TemplateRenderer):
    def render(self, template_content: bytes, data: dict[str, object]) -> RenderResult:
        placeholder_keys, all_keys = _extract_template_keys(template_content)
        provided_keys = set(data.keys())
        missing_keys = sorted(all_keys - provided_keys)

        # Build render_data: pre-fill ALL template variables with safe defaults
        # so Relatorio never encounters Undefined.
        render_data: dict[str, object] = {}
        for key in all_keys:
            if key in data:
                render_data[key] = _normalize_value(data[key])
            elif key in placeholder_keys:
                # Missing placeholder → keep visible in document
                render_data[key] = f"<{key}>"
            else:
                # Missing if-condition or for-iterable → safe default
                render_data[key] = ""

        # Pass through extra keys from data (not detected in template)
        for key, value in data.items():
            if key not in render_data:
                render_data[key] = _normalize_value(value)

        with tempfile.NamedTemporaryFile(suffix=".odt", delete=False) as tmp:
            tmp.write(template_content)
            tmp_path = Path(tmp.name)

        try:
            template = Template(source="", filepath=str(tmp_path))
            output = template.generate(**render_data).render()
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
