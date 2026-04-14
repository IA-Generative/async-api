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
    def test_all_placeholders_replaced(self) -> None:
        renderer = OdtRenderer()
        data = _load_data()

        result = renderer.render(_load_template(), data)

        content = _extract_content_xml(result.content)
        assert "${nom}" not in content
        assert "${ville}" not in content
        assert "Dupont" in content
        assert "Nice" in content

    def test_no_warnings_for_provided_keys(self) -> None:
        renderer = OdtRenderer()
        data = _load_data()

        result = renderer.render(_load_template(), data)

        assert not any("nom" in w for w in result.warnings)
        assert not any("ville" in w for w in result.warnings)

    def test_output_is_valid_odt(self) -> None:
        renderer = OdtRenderer()
        data = _load_data()

        result = renderer.render(_load_template(), data)

        with zipfile.ZipFile(BytesIO(result.content), "r") as z:
            assert "content.xml" in z.namelist()
            assert "mimetype" in z.namelist()


class TestOdtRendererMissingKeys:
    def test_missing_key_leaves_placeholder(self) -> None:
        renderer = OdtRenderer()
        partial_data = {"nom": "Dupont"}

        result = renderer.render(_load_template(), partial_data)

        content = _extract_content_xml(result.content)
        assert "Dupont" in content
        assert "${ville}" in content

    def test_missing_key_generates_warning(self) -> None:
        renderer = OdtRenderer()
        partial_data = {"nom": "Dupont"}

        result = renderer.render(_load_template(), partial_data)

        assert any("ville" in w for w in result.warnings)

    def test_empty_data_leaves_all_placeholders(self) -> None:
        renderer = OdtRenderer()

        result = renderer.render(_load_template(), {})

        content = _extract_content_xml(result.content)
        assert "${nom}" in content
        assert "${ville}" in content
        assert len(result.warnings) >= 2


class TestOdtRendererEdgeCases:
    def test_extra_keys_ignored(self) -> None:
        renderer = OdtRenderer()
        data = {**_load_data(), "unknown_key": "ignored"}

        result = renderer.render(_load_template(), data)

        assert not any("unknown_key" in w for w in result.warnings)
        assert "ignored" not in _extract_content_xml(result.content)
