"""Tests pour `api/docs/code_samples.py`.

Stratégie : on construit des fragments OpenAPI synthétiques minimaux et on
vérifie l'output de `inject_code_samples` sur les morceaux porteurs de
sémantique (auth, body, params, URL). On évite les snapshots complets — la
mise en forme exacte (indentation, espacement) est un détail d'implémentation.
"""

from typing import Any

import pytest

from api.docs.code_samples import (
    REDOC_CODE_SAMPLES_KEY,
    CodeSampleLang,
    inject_code_samples,
)


def _operation(**overrides: object) -> dict[str, Any]:
    return {"summary": "test op", **overrides}


def _schema(
    path: str,
    method: str,
    operation: dict[str, Any],
    components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"paths": {path: {method: operation}}}
    if components is not None:
        schema["components"] = components
    return schema


def _samples_by_lang(
    schema: dict[str, Any],
    path: str,
    method: str,
) -> dict[CodeSampleLang, str]:
    inject_code_samples(schema)
    samples = schema["paths"][path][method][REDOC_CODE_SAMPLES_KEY]
    return {CodeSampleLang(s["lang"]): s["source"] for s in samples}


# ── Structure de l'injection ──────────────────────────────────────────────


def test_injects_python_and_typescript_in_that_order() -> None:
    schema = _schema("/foo", "get", _operation())
    inject_code_samples(schema)
    samples = schema["paths"]["/foo"]["get"][REDOC_CODE_SAMPLES_KEY]
    assert [s["lang"] for s in samples] == [
        CodeSampleLang.PYTHON.value,
        CodeSampleLang.TYPESCRIPT.value,
    ]
    for sample in samples:
        assert {"lang", "label", "source"} <= sample.keys()
        assert sample["source"].strip()  # non vide


def test_no_paths_does_not_raise() -> None:
    inject_code_samples({})


def test_skips_non_method_keys_at_path_level() -> None:
    schema: dict[str, Any] = {
        "paths": {
            "/foo": {
                "parameters": [{"name": "x", "in": "query"}],
                "summary": "shared",
                "get": _operation(),
            },
        },
    }
    inject_code_samples(schema)
    assert REDOC_CODE_SAMPLES_KEY in schema["paths"]["/foo"]["get"]
    assert schema["paths"]["/foo"]["parameters"] == [{"name": "x", "in": "query"}]
    assert schema["paths"]["/foo"]["summary"] == "shared"


def test_skips_non_dict_operations() -> None:
    schema: dict[str, Any] = {"paths": {"/foo": {"get": "not a dict"}}}
    inject_code_samples(schema)
    assert schema["paths"]["/foo"]["get"] == "not a dict"


def test_inject_is_idempotent_replacing_not_duplicating() -> None:
    schema = _schema("/foo", "get", _operation())
    inject_code_samples(schema)
    inject_code_samples(schema)
    assert len(schema["paths"]["/foo"]["get"][REDOC_CODE_SAMPLES_KEY]) == 2


# ── Auth ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "security",
    [None, [], [{}]],
    ids=["absent", "empty-list", "list-with-empty-entry"],
)
def test_security_without_credentials_omits_auth(
    security: list[dict[str, Any]] | None,
) -> None:
    op = _operation()
    if security is not None:
        op["security"] = security
    samples = _samples_by_lang(_schema("/x", "get", op), "/x", "get")
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert "CLIENT_ID" not in py
    assert "auth=" not in py
    assert "btoa" not in ts
    assert "Authorization" not in ts


@pytest.mark.parametrize(
    "security",
    [[{"basicAuth": []}], [{"basicAuth": []}, {}]],
    ids=["single-scheme", "scheme-mixed-with-empty-entry"],
)
def test_security_with_credentials_wires_auth(
    security: list[dict[str, Any]],
) -> None:
    op = _operation(security=security)
    samples = _samples_by_lang(_schema("/x", "get", op), "/x", "get")
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert "CLIENT_ID" in py
    assert "auth=(CLIENT_ID, CLIENT_SECRET)" in py
    assert "btoa(`${CLIENT_ID}:${CLIENT_SECRET}`)" in ts
    assert '"Authorization": authHeader' in ts


# ── URL : path / query params ──────────────────────────────────────────────


def test_no_path_params_uses_string_concat_in_python_and_template_in_ts() -> None:
    samples = _samples_by_lang(_schema("/health", "get", _operation()), "/health", "get")
    assert 'BASE_URL + "/health"' in samples[CodeSampleLang.PYTHON]
    assert "`${BASE_URL}/health`" in samples[CodeSampleLang.TYPESCRIPT]


def test_path_params_become_variables_and_interpolated_url() -> None:
    op = _operation(
        parameters=[
            {"name": "service", "in": "path"},
            {"name": "task_id", "in": "path"},
        ],
    )
    path = "/v1/services/{service}/tasks/{task_id}"
    samples = _samples_by_lang(_schema(path, "get", op), path, "get")
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert 'service = "<service>"' in py
    assert 'task_id = "<task_id>"' in py
    assert 'f"{BASE_URL}/v1/services/{service}/tasks/{task_id}"' in py
    assert 'const service = "<service>";' in ts
    assert "`${BASE_URL}/v1/services/${service}/tasks/${task_id}`" in ts


def test_query_params_python_dict_typescript_urlsearchparams() -> None:
    op = _operation(
        parameters=[
            {"name": "from", "in": "query"},
            {"name": "to", "in": "query"},
        ],
    )
    samples = _samples_by_lang(_schema("/usage", "get", op), "/usage", "get")
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert "params = " in py
    assert "params=params" in py
    assert "URLSearchParams(" in ts
    assert "?${query.toString()}" in ts


def test_non_dict_parameter_entries_are_silently_skipped() -> None:
    """OpenAPI bizarre/cassé : un entry non-dict dans `parameters` ne doit pas planter."""
    op = _operation(
        parameters=[
            "not-a-dict",
            {"name": "service", "in": "path"},
        ],
    )
    samples = _samples_by_lang(
        _schema("/v1/services/{service}", "get", op),
        "/v1/services/{service}",
        "get",
    )
    assert 'service = "<service>"' in samples[CodeSampleLang.PYTHON]


def test_parameter_without_name_is_silently_skipped() -> None:
    """Cas pathologique : un paramètre OpenAPI sans `name` ne doit pas planter."""
    op = _operation(
        parameters=[
            {"in": "path"},  # no name
            {"name": "service", "in": "path"},
        ],
    )
    samples = _samples_by_lang(
        _schema("/v1/services/{service}", "get", op),
        "/v1/services/{service}",
        "get",
    )
    py = samples[CodeSampleLang.PYTHON]
    assert 'service = "<service>"' in py
    # Aucun var name foireux genre `None = "..."`
    assert "None = " not in py


# ── Body : JSON ────────────────────────────────────────────────────────────


def test_post_with_inline_json_example() -> None:
    op = _operation(
        requestBody={"content": {"application/json": {"example": {"k": "v"}}}},
    )
    samples = _samples_by_lang(_schema("/x", "post", op), "/x", "post")
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert "body = {'k': 'v'}" in py
    assert "json=body" in py
    assert '"k": "v"' in ts
    assert '"Content-Type": "application/json"' in ts
    assert "JSON.stringify(body)" in ts


def test_post_with_examples_plural_uses_first_value() -> None:
    op = _operation(
        requestBody={
            "content": {
                "application/json": {
                    "examples": {
                        "default": {"value": {"k": "v"}},
                        "other": {"value": {"k": "z"}},
                    },
                },
            },
        },
    )
    samples = _samples_by_lang(_schema("/x", "post", op), "/x", "post")
    assert "{'k': 'v'}" in samples[CodeSampleLang.PYTHON]
    assert "{'k': 'z'}" not in samples[CodeSampleLang.PYTHON]


def test_post_resolves_example_via_schema_ref() -> None:
    op = _operation(
        requestBody={
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/MyBody"}},
            },
        },
    )
    schema = _schema(
        "/x",
        "post",
        op,
        components={"schemas": {"MyBody": {"type": "object", "example": {"k": "ref"}}}},
    )
    samples = _samples_by_lang(schema, "/x", "post")
    assert "'k': 'ref'" in samples[CodeSampleLang.PYTHON]


@pytest.mark.parametrize(
    "ref",
    [
        "#/components/schemas/Missing",  # ref does not resolve
        "external://nope.json#/Foo",  # not a local ref
    ],
)
def test_post_with_unresolvable_ref_falls_back_to_empty_body(ref: str) -> None:
    op = _operation(
        requestBody={"content": {"application/json": {"schema": {"$ref": ref}}}},
    )
    samples = _samples_by_lang(_schema("/x", "post", op), "/x", "post")
    assert "body = {}" in samples[CodeSampleLang.PYTHON]
    assert "const body = {};" in samples[CodeSampleLang.TYPESCRIPT]


def test_ref_traversal_through_non_dict_node_falls_back_to_empty_body() -> None:
    """`$ref` qui plonge dans un nœud non-dict (ex: dans une string) → fallback `{}`."""
    op = _operation(
        requestBody={
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/MyBody/title/extra"},
                },
            },
        },
    )
    schema = _schema(
        "/x",
        "post",
        op,
        components={"schemas": {"MyBody": {"title": "a string, not a dict"}}},
    )
    samples = _samples_by_lang(schema, "/x", "post")
    assert "body = {}" in samples[CodeSampleLang.PYTHON]


def test_post_without_request_body_falls_back_to_empty_json() -> None:
    samples = _samples_by_lang(_schema("/x", "post", _operation()), "/x", "post")
    assert "body = {}" in samples[CodeSampleLang.PYTHON]
    assert "json=body" in samples[CodeSampleLang.PYTHON]
    assert '"Content-Type": "application/json"' in samples[CodeSampleLang.TYPESCRIPT]


@pytest.mark.parametrize("method", ["get", "delete"])
def test_get_and_delete_have_no_body(method: str) -> None:
    samples = _samples_by_lang(_schema("/x", method, _operation()), "/x", method)
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert "body = " not in py
    assert "json=body" not in py
    assert "const body" not in ts
    assert '"Content-Type"' not in ts


# ── Body : multipart ──────────────────────────────────────────────────────


def test_multipart_uploads_use_form_data_and_no_content_type_header() -> None:
    op = _operation(
        security=[{"basicAuth": []}],
        requestBody={"content": {"multipart/form-data": {}}},
    )
    samples = _samples_by_lang(_schema("/upload", "post", op), "/upload", "post")
    py = samples[CodeSampleLang.PYTHON]
    ts = samples[CodeSampleLang.TYPESCRIPT]
    assert 'files = {"file": open(' in py
    assert "files=files" in py
    assert "json=body" not in py
    assert "FormData()" in ts
    assert "body: form" in ts
    # Le navigateur calcule le boundary lui-même : ne pas forcer Content-Type.
    assert '"Content-Type"' not in ts
    # Auth doit toujours être posée séparément.
    assert '"Authorization": authHeader' in ts
