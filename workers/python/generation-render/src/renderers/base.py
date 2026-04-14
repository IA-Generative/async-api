from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RenderResult:
    content: bytes
    warnings: list[str] = field(default_factory=list)


class TemplateRenderer(ABC):
    @abstractmethod
    def render(self, template_content: bytes, data: dict[str, str]) -> RenderResult:
        """Replace placeholders in the template with the provided data.

        Args:
            template_content: Raw bytes of the template file.
            data: Key-value pairs to substitute in the template.

        Returns:
            RenderResult with the rendered content and any warnings
            for missing keys.
        """
