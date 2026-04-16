from src.renderers.odt import _normalize_value


class TestNormalizeValueBooleans:
    def test_true_returns_true_string(self) -> None:
        assert _normalize_value(True) == "true"

    def test_false_returns_empty_string(self) -> None:
        assert _normalize_value(False) == ""


class TestNormalizeValueStrings:
    def test_string_unchanged(self) -> None:
        assert _normalize_value("Nice") == "Nice"

    def test_empty_string_unchanged(self) -> None:
        assert _normalize_value("") == ""


class TestNormalizeValueLists:
    def test_list_passed_through(self) -> None:
        items = ["a", "b", "c"]
        assert _normalize_value(items) == ["a", "b", "c"]

    def test_empty_list_passed_through(self) -> None:
        assert _normalize_value([]) == []


class TestNormalizeValueOtherTypes:
    def test_int_converted_to_string(self) -> None:
        assert _normalize_value(42) == "42"

    def test_float_converted_to_string(self) -> None:
        assert _normalize_value(3.14) == "3.14"

    def test_none_converted_to_string(self) -> None:
        assert _normalize_value(None) == "None"
