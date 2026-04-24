"""Génération de snippets Python / TypeScript pour ReDoc.

ReDoc supporte l'extension OpenAPI `x-codeSamples` : pour chaque opération,
on peut fournir une liste d'exemples de code que l'utilisateur copie-colle.

Ce module parcourt le schéma OpenAPI enrichi et injecte, pour chaque route
BRIO, un snippet Python (via `requests`) et un snippet TypeScript (via
`fetch`). L'objectif est de faciliter l'adoption de l'API sans générer de
client : le développeur a immédiatement un exemple exécutable.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pprint import pformat
from typing import Any, TypedDict

REDOC_CODE_SAMPLES_KEY = "x-codeSamples"

_HTTP_METHODS = ("get", "post", "put", "delete", "patch")
_JSON_CONTENT_TYPE = "application/json"
_MULTIPART_CONTENT_TYPE = "multipart/form-data"

_BASE_URL_PLACEHOLDER = "https://<host>"
_CLIENT_ID_PLACEHOLDER = "<client_id>"
_CLIENT_SECRET_PLACEHOLDER = "<client_secret>"  # noqa: S105 — placeholder shown in docs


class CodeSampleLang(StrEnum):
    PYTHON = "Python"
    TYPESCRIPT = "TypeScript"


class CodeSample(TypedDict):
    lang: str
    label: str
    source: str


class _ParamInfo(TypedDict):
    name: str
    placeholder: str


def inject_code_samples(schema: dict[str, Any]) -> None:
    """Ajoute `x-codeSamples` à toutes les opérations du schéma OpenAPI.

    Modifie le schéma en place. Sans effet si `schema` n'a pas de `paths`.
    """
    paths: dict[str, Any] = schema.get("paths", {})
    for path, item in paths.items():
        for method, operation in item.items():
            if method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation[REDOC_CODE_SAMPLES_KEY] = _build_samples(
                method=method,
                path=path,
                operation=operation,
                full_schema=schema,
            )


def _build_samples(
    method: str,
    path: str,
    operation: dict[str, Any],
    full_schema: dict[str, Any],
) -> list[CodeSample]:
    context = _OperationContext.from_operation(
        method=method,
        path=path,
        operation=operation,
        full_schema=full_schema,
    )
    return [
        CodeSample(
            lang=CodeSampleLang.PYTHON.value,
            label="Python (requests)",
            source=_render_python(context),
        ),
        CodeSample(
            lang=CodeSampleLang.TYPESCRIPT.value,
            label="TypeScript (fetch)",
            source=_render_typescript(context),
        ),
    ]


class _OperationContext:
    """Contexte agrégé pour la génération de snippets."""

    def __init__(
        self,
        *,
        method: str,
        path: str,
        needs_auth: bool,
        path_params: list[_ParamInfo],
        query_params: list[_ParamInfo],
        json_body_example: object | None,
        is_multipart: bool,
    ) -> None:
        self.method = method
        self.path = path
        self.needs_auth = needs_auth
        self.path_params = path_params
        self.query_params = query_params
        self.json_body_example = json_body_example
        self.is_multipart = is_multipart

    @classmethod
    def from_operation(
        cls,
        *,
        method: str,
        path: str,
        operation: dict[str, Any],
        full_schema: dict[str, Any],
    ) -> _OperationContext:
        path_params, query_params = _collect_parameters(operation)
        content = operation.get("requestBody", {}).get("content", {})
        is_multipart = _MULTIPART_CONTENT_TYPE in content
        body_example = (
            _extract_json_example(operation, full_schema)
            if _JSON_CONTENT_TYPE in content
            else None
        )
        return cls(
            method=method,
            path=path,
            needs_auth=_needs_auth(operation),
            path_params=path_params,
            query_params=query_params,
            json_body_example=body_example,
            is_multipart=is_multipart,
        )


def _collect_parameters(operation: dict[str, Any]) -> tuple[list[_ParamInfo], list[_ParamInfo]]:
    path_params: list[_ParamInfo] = []
    query_params: list[_ParamInfo] = []
    for param in operation.get("parameters", []):
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if not isinstance(name, str):
            continue
        info: _ParamInfo = {"name": name, "placeholder": f"<{name}>"}
        location = param.get("in")
        if location == "path":
            path_params.append(info)
        elif location == "query":
            query_params.append(info)
    return path_params, query_params


def _needs_auth(operation: dict[str, Any]) -> bool:
    security = operation.get("security")
    if not isinstance(security, list):
        return False
    return any(bool(entry) for entry in security)


def _extract_json_example(operation: dict[str, Any], full_schema: dict[str, Any]) -> object | None:
    json_content = (
        operation.get("requestBody", {}).get("content", {}).get(_JSON_CONTENT_TYPE, {})
    )
    if "example" in json_content:
        return json_content["example"]
    examples = json_content.get("examples")
    if isinstance(examples, dict) and examples:
        first = next(iter(examples.values()))
        if isinstance(first, dict) and "value" in first:
            return first["value"]
    schema = json_content.get("schema", {})
    ref = schema.get("$ref") if isinstance(schema, dict) else None
    if isinstance(ref, str):
        resolved = _resolve_ref(ref, full_schema)
        if "example" in resolved:
            return resolved["example"]
    return None


def _resolve_ref(ref: str, full_schema: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    node: Any = full_schema
    for part in ref[2:].split("/"):
        if not isinstance(node, dict):
            return {}
        node = node.get(part)
        if node is None:
            return {}
    return node if isinstance(node, dict) else {}


def _python_path_expr(path: str, path_params: list[_ParamInfo]) -> str:
    """Transforme `/v1/services/{service}/tasks/{task_id}` en f-string Python."""
    if not path_params:
        return f'BASE_URL + "{path}"'
    return f'f"{{BASE_URL}}{path}"'


def _typescript_path_expr(path: str, path_params: list[_ParamInfo]) -> str:
    """Transforme le path en template literal TypeScript."""
    if not path_params:
        return f"`${{BASE_URL}}{path}`"
    ts_path = path
    for param in path_params:
        ts_path = ts_path.replace(f"{{{param['name']}}}", f"${{{param['name']}}}")
    return f"`${{BASE_URL}}{ts_path}`"


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


def _render_python(ctx: _OperationContext) -> str:
    lines: list[str] = ["import requests", ""]
    lines.append(f'BASE_URL = "{_BASE_URL_PLACEHOLDER}"')
    if ctx.needs_auth:
        lines.append(f'CLIENT_ID = "{_CLIENT_ID_PLACEHOLDER}"')
        lines.append(f'CLIENT_SECRET = "{_CLIENT_SECRET_PLACEHOLDER}"')
    lines.append("")

    for param in ctx.path_params:
        lines.append(f'{param["name"]} = "{param["placeholder"]}"')
    if ctx.path_params:
        lines.append("")

    kwargs: list[str] = []
    if ctx.needs_auth:
        kwargs.append("auth=(CLIENT_ID, CLIENT_SECRET)")

    if ctx.query_params:
        params_dict = {p["name"]: p["placeholder"] for p in ctx.query_params}
        lines.append(f"params = {pformat(params_dict, indent=4, sort_dicts=False, width=100)}")
        lines.append("")
        kwargs.append("params=params")

    if ctx.is_multipart:
        lines.append('files = {"file": open("<path/to/file>", "rb")}')
        lines.append("")
        kwargs.append("files=files")
    elif ctx.json_body_example is not None:
        body_literal = pformat(ctx.json_body_example, indent=4, sort_dicts=False, width=100)
        lines.append(f"body = {body_literal}")
        lines.append("")
        kwargs.append("json=body")
    elif _supports_json_body(ctx.method):
        lines.append("body = {}")
        lines.append("")
        kwargs.append("json=body")

    url_expr = _python_path_expr(ctx.path, ctx.path_params)
    call_args = ", ".join([url_expr, *kwargs])
    lines.append(f"response = requests.{ctx.method}({call_args})")
    lines.append("response.raise_for_status()")
    lines.append("print(response.json())")
    return "\n".join(lines)


def _render_typescript(ctx: _OperationContext) -> str:
    lines: list[str] = [
        f'const BASE_URL = "{_BASE_URL_PLACEHOLDER}";',
    ]
    if ctx.needs_auth:
        lines.append(f'const CLIENT_ID = "{_CLIENT_ID_PLACEHOLDER}";')
        lines.append(f'const CLIENT_SECRET = "{_CLIENT_SECRET_PLACEHOLDER}";')
    lines.append("")

    for param in ctx.path_params:
        lines.append(f'const {param["name"]} = "{param["placeholder"]}";')
    if ctx.path_params:
        lines.append("")

    headers: list[str] = []
    if ctx.needs_auth:
        lines.append(
            'const authHeader = "Basic " + btoa(`${CLIENT_ID}:${CLIENT_SECRET}`);',
        )
        lines.append("")
        headers.append('"Authorization": authHeader')

    url_expr = _typescript_path_expr(ctx.path, ctx.path_params)
    if ctx.query_params:
        query_dict = {p["name"]: p["placeholder"] for p in ctx.query_params}
        lines.append(f"const query = new URLSearchParams({json.dumps(query_dict, ensure_ascii=False)});")
        lines.append("")
        url_expr = f"`{url_expr[1:-1]}?${{query.toString()}}`"

    body_var: str | None = None
    if ctx.is_multipart:
        lines.append("const form = new FormData();")
        lines.append('form.append("file", file); // `file`: File or Blob à uploader')
        lines.append("")
        body_var = "form"
    elif ctx.json_body_example is not None:
        body_literal = json.dumps(ctx.json_body_example, indent=2, ensure_ascii=False)
        lines.append(f"const body = {body_literal};")
        lines.append("")
        headers.append('"Content-Type": "application/json"')
        body_var = "JSON.stringify(body)"
    elif _supports_json_body(ctx.method):
        lines.append("const body = {};")
        lines.append("")
        headers.append('"Content-Type": "application/json"')
        body_var = "JSON.stringify(body)"

    fetch_options: list[str] = [f'method: "{ctx.method.upper()}"']
    if headers:
        fetch_options.append("headers: {\n" + _indent(",\n".join(headers), 4) + "\n  }")
    if body_var:
        fetch_options.append(f"body: {body_var}")

    options_block = ",\n  ".join(fetch_options)
    lines.append(f"const response = await fetch({url_expr}, {{")
    lines.append(f"  {options_block},")
    lines.append("});")
    lines.append("if (!response.ok) throw new Error(`HTTP ${response.status}`);")
    lines.append("const data = await response.json();")
    lines.append("console.log(data);")
    return "\n".join(lines)


def _supports_json_body(method: str) -> bool:
    return method in ("post", "put", "patch")
