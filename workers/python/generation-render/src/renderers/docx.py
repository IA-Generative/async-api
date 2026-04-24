from io import BytesIO

from docxtpl import DocxTemplate
from jinja2 import DebugUndefined, Environment
from loguru import logger

from src.renderers.base import RenderResult, TemplateRenderer


class DocxRenderer(TemplateRenderer):
    def render(self, template_content: bytes, data: dict[str, object]) -> RenderResult:
        template = DocxTemplate(BytesIO(template_content))
        jinja_env = Environment(undefined=DebugUndefined)  # noqa: S701

        expected_keys = template.get_undeclared_template_variables(jinja_env=jinja_env)
        missing_keys = sorted(expected_keys - data.keys())

        template.render(data, jinja_env=jinja_env)
        output = BytesIO()
        template.save(output)

        warnings = [f"La donnée pour '{key}' n'est pas définie" for key in missing_keys]
        if warnings:
            logger.warning(f"Missing keys: {missing_keys}")

        return RenderResult(content=output.getvalue(), warnings=warnings)
