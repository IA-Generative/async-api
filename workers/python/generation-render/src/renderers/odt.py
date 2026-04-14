import re
import zipfile
from io import BytesIO

from loguru import logger

from src.renderers.base import RenderResult, TemplateRenderer

PLACEHOLDER_PATTERN = re.compile(r"\$\{(\w+)\}")


class OdtRenderer(TemplateRenderer):
    def render(self, template_content: bytes, data: dict[str, str]) -> RenderResult:
        warnings: list[str] = []
        template_zip = BytesIO(template_content)
        output_zip = BytesIO()

        with zipfile.ZipFile(template_zip, "r") as zin, zipfile.ZipFile(output_zip, "w") as zout:
            for item in zin.infolist():
                content = zin.read(item.filename)

                if item.filename == "content.xml":
                    content = self._replace_placeholders(
                        content.decode("utf-8"),
                        data,
                        warnings,
                    ).encode("utf-8")

                zout.writestr(item, content)

        if warnings:
            logger.warning(f"Missing keys: {warnings}")

        return RenderResult(content=output_zip.getvalue(), warnings=warnings)

    def _replace_placeholders(
        self,
        xml_content: str,
        data: dict[str, str],
        warnings: list[str],
    ) -> str:
        def replace_match(match: re.Match) -> str:
            key = match.group(1)
            if key in data:
                return data[key]
            warnings.append(f"La donnée pour '{key}' n'est pas définie")
            return match.group(0)

        return PLACEHOLDER_PATTERN.sub(replace_match, xml_content)
