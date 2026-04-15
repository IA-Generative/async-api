import json
import zipfile
from io import BytesIO
from pathlib import Path

from src.renderers.odt import OdtRenderer

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_template() -> bytes:
    return (FIXTURES_DIR / "test_template.odt").read_bytes()


def _load_data() -> dict:
    return json.loads((FIXTURES_DIR / "test_data.json").read_text())


def _extract_content_xml(odt_bytes: bytes) -> str:
    with zipfile.ZipFile(BytesIO(odt_bytes), "r") as z:
        return z.read("content.xml").decode("utf-8")


class TestOdtRendererHappyPath:
    def test_simple_placeholders_replaced(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), _load_data())

        content = _extract_content_xml(result.content)
        assert "Dupont" in content
        assert "Nice" in content

    def test_conditional_block_rendered(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), _load_data())

        content = _extract_content_xml(result.content)
        assert "Vous etes administrateur" in content

    def test_iterative_block_rendered(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), _load_data())

        content = _extract_content_xml(result.content)
        assert "dossier-001" in content
        assert "dossier-002" in content
        assert "dossier-003" in content

    def test_no_warnings_when_all_keys_present(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), _load_data())

        assert result.warnings == []

    def test_output_is_valid_odt(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), _load_data())

        with zipfile.ZipFile(BytesIO(result.content), "r") as z:
            assert "content.xml" in z.namelist()
            assert "mimetype" in z.namelist()
            assert "meta.xml" in z.namelist()


class TestOdtRendererMissingKeys:
    def test_missing_simple_key_renders_empty(self) -> None:
        """In lenient mode, Relatorio renders missing keys as empty strings.

        The warning is the signal that a key was missing, not the document content.
        """
        renderer = OdtRenderer()

        result = renderer.render(
            _load_template(),
            {"nom": "Dupont", "is_admin": True, "items": []},
        )

        content = _extract_content_xml(result.content)
        assert "Dupont" in content
        assert any("ville" in w for w in result.warnings)

    def test_missing_key_generates_warning(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(
            _load_template(),
            {"nom": "Dupont", "is_admin": True, "items": []},
        )

        assert any("ville" in w for w in result.warnings)

    def test_multiple_missing_keys(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), {})

        assert any("nom" in w for w in result.warnings)
        assert any("ville" in w for w in result.warnings)


class TestOdtRendererEdgeCases:
    def test_extra_keys_ignored(self) -> None:
        renderer = OdtRenderer()
        data = {**_load_data(), "unknown_key": "ignored"}

        result = renderer.render(_load_template(), data)

        assert result.warnings == []
        assert "ignored" not in _extract_content_xml(result.content)

    def test_conditional_empty_hides_block(self) -> None:
        """Template uses is_admin!='' so empty string hides the block."""
        renderer = OdtRenderer()
        data = {**_load_data(), "is_admin": ""}

        result = renderer.render(_load_template(), data)

        content = _extract_content_xml(result.content)
        assert "Vous etes administrateur" not in content

    def test_empty_list_produces_no_items(self) -> None:
        renderer = OdtRenderer()
        data = {**_load_data(), "items": []}

        result = renderer.render(_load_template(), data)

        content = _extract_content_xml(result.content)
        assert "dossier" not in content
