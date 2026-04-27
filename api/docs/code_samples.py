"""Génération de snippets Python / TypeScript pour ReDoc.

ReDoc supporte l'extension OpenAPI `x-codeSamples` : pour chaque opération,
on fournit une liste d'exemples de code que l'utilisateur copie-colle.

Pipeline :

    operation OpenAPI ─► _RequestPlan ─► snippet (Python | TypeScript)

`_RequestPlan` est une représentation neutre, indépendante du langage, de ce
qu'il faut rendre. Chaque renderer langage le consomme et compose le snippet
à partir de petites sections nommées (constantes, body, appel HTTP, …) qu'un
helper `_join_sections` réassemble avec une ligne vide entre. Pas de
`lines.append` éparpillés à travers une fonction de 80 lignes.

Pour ajouter un langage : écrire `_render_<lang>(plan) -> str` qui compose
ses sections, et l'enregistrer dans `_RENDERERS`.
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pprint import pformat
from typing import Any, Self, TypedDict

REDOC_CODE_SAMPLES_KEY = "x-codeSamples"

_ALL_HTTP_METHODS = frozenset({"get", "post", "put", "delete", "patch"})
_BODY_BEARING_METHODS = frozenset({"post", "put", "patch"})
_JSON_CONTENT_TYPE = "application/json"
_MULTIPART_CONTENT_TYPE = "multipart/form-data"

_BASE_URL_PLACEHOLDER = "https://<host>"
_CLIENT_ID_PLACEHOLDER = "<client_id>"
_CLIENT_SECRET_PLACEHOLDER = "<client_secret>"  # noqa: S105 — placeholder shown in docs

_PY_LITERAL_WIDTH = 100
_TS_INDENT = "  "


class CodeSampleLang(StrEnum):
    PYTHON = "Python"
    TYPESCRIPT = "TypeScript"


class CodeSample(TypedDict):
    lang: str
    label: str
    source: str


@dataclass(frozen=True, slots=True)
class _ParamInfo:
    name: str
    placeholder: str


# ── Body : union discriminée ───────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class _NoBody:
    """Pas de body (GET/DELETE sans corps)."""


@dataclass(frozen=True, slots=True)
class _MultipartBody:
    """Upload de fichier (`multipart/form-data`)."""


@dataclass(frozen=True, slots=True)
class _JsonBody:
    """Body JSON. `example is None` ⇒ on rend `{}` ; sinon on rend l'exemple."""

    example: object | None


_Body = _NoBody | _MultipartBody | _JsonBody


# ── Plan de requête : représentation neutre ────────────────────────────────


@dataclass(frozen=True, slots=True)
class _RequestPlan:
    """Données suffisantes pour rendre un snippet, indépendantes du langage."""

    method: str
    path: str
    needs_auth: bool
    path_params: tuple[_ParamInfo, ...]
    query_params: tuple[_ParamInfo, ...]
    body: _Body

    @classmethod
    def from_operation(
        cls,
        *,
        method: str,
        path: str,
        operation: dict[str, Any],
        full_schema: dict[str, Any],
    ) -> Self:
        path_params, query_params = _collect_parameters(operation)
        return cls(
            method=method,
            path=path,
            needs_auth=_needs_auth(operation),
            path_params=path_params,
            query_params=query_params,
            body=_resolve_body(operation, full_schema, method),
        )


# ── API publique ───────────────────────────────────────────────────────────


def inject_code_samples(schema: dict[str, Any]) -> None:
    """Ajoute `x-codeSamples` à toutes les opérations du schéma OpenAPI.

    Modifie le schéma en place. Sans effet si `schema` n'a pas de `paths`.
    """
    paths: dict[str, Any] = schema.get("paths", {})
    for path, item in paths.items():
        for method, operation in item.items():
            if method not in _ALL_HTTP_METHODS or not isinstance(operation, dict):
                continue
            plan = _RequestPlan.from_operation(
                method=method,
                path=path,
                operation=operation,
                full_schema=schema,
            )
            operation[REDOC_CODE_SAMPLES_KEY] = [
                CodeSample(lang=lang.value, label=label, source=render(plan)) for lang, label, render in _RENDERERS
            ]


# ── Extraction du plan depuis l'OpenAPI ────────────────────────────────────


def _collect_parameters(
    operation: dict[str, Any],
) -> tuple[tuple[_ParamInfo, ...], tuple[_ParamInfo, ...]]:
    path_params: list[_ParamInfo] = []
    query_params: list[_ParamInfo] = []
    for param in operation.get("parameters", []):
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if not isinstance(name, str):
            continue
        info = _ParamInfo(name=name, placeholder=f"<{name}>")
        match param.get("in"):
            case "path":
                path_params.append(info)
            case "query":
                query_params.append(info)
    return tuple(path_params), tuple(query_params)


def _needs_auth(operation: dict[str, Any]) -> bool:
    security = operation.get("security")
    return isinstance(security, list) and any(bool(entry) for entry in security)


def _resolve_body(
    operation: dict[str, Any],
    full_schema: dict[str, Any],
    method: str,
) -> _Body:
    content = operation.get("requestBody", {}).get("content", {})
    if _MULTIPART_CONTENT_TYPE in content:
        return _MultipartBody()
    if _JSON_CONTENT_TYPE in content:
        return _JsonBody(example=_extract_json_example(content[_JSON_CONTENT_TYPE], full_schema))
    if method in _BODY_BEARING_METHODS:
        return _JsonBody(example=None)
    return _NoBody()


def _extract_json_example(
    json_content: dict[str, Any],
    full_schema: dict[str, Any],
) -> object | None:
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


# ── Helper de composition ──────────────────────────────────────────────────


def _join_sections(sections: list[str]) -> str:
    """Concatène les sections non vides, séparées par une ligne vide."""
    return "\n\n".join(section for section in sections if section)


# ── Renderer Python ────────────────────────────────────────────────────────


def _render_python(plan: _RequestPlan) -> str:
    return _join_sections(
        [
            "import requests",
            _py_constants(plan),
            _py_path_param_vars(plan),
            _py_query_dict(plan),
            _py_body(plan),
            _py_request_call(plan),
        ],
    )


def _py_constants(plan: _RequestPlan) -> str:
    lines = [f'BASE_URL = "{_BASE_URL_PLACEHOLDER}"']
    if plan.needs_auth:
        lines.append(f'CLIENT_ID = "{_CLIENT_ID_PLACEHOLDER}"')
        lines.append(f'CLIENT_SECRET = "{_CLIENT_SECRET_PLACEHOLDER}"')
    return "\n".join(lines)


def _py_path_param_vars(plan: _RequestPlan) -> str:
    return "\n".join(f'{p.name} = "{p.placeholder}"' for p in plan.path_params)


def _py_query_dict(plan: _RequestPlan) -> str:
    if not plan.query_params:
        return ""
    params = {p.name: p.placeholder for p in plan.query_params}
    return f"params = {_py_literal(params)}"


def _py_body(plan: _RequestPlan) -> str:
    match plan.body:
        case _MultipartBody():
            return 'files = {"file": open("<path/to/file>", "rb")}'
        case _JsonBody(example=None):
            return "body = {}"
        case _JsonBody(example=ex):
            return f"body = {_py_literal(ex)}"
        case _NoBody():
            return ""


def _py_request_call(plan: _RequestPlan) -> str:
    url_expr = f'f"{{BASE_URL}}{plan.path}"' if plan.path_params else f'BASE_URL + "{plan.path}"'
    args = [url_expr]
    if plan.needs_auth:
        args.append("auth=(CLIENT_ID, CLIENT_SECRET)")
    if plan.query_params:
        args.append("params=params")
    match plan.body:
        case _MultipartBody():
            args.append("files=files")
        case _JsonBody():
            args.append("json=body")
        case _NoBody():
            pass
    return "\n".join(
        [
            f"response = requests.{plan.method}({', '.join(args)})",
            "response.raise_for_status()",
            "print(response.json())",
        ],
    )


def _py_literal(value: object) -> str:
    return pformat(value, indent=4, sort_dicts=False, width=_PY_LITERAL_WIDTH)


# ── Renderer TypeScript ────────────────────────────────────────────────────


def _render_typescript(plan: _RequestPlan) -> str:
    return _join_sections(
        [
            _ts_constants(plan),
            _ts_path_param_vars(plan),
            _ts_auth_header(plan),
            _ts_query_setup(plan),
            _ts_body(plan),
            _ts_fetch_call(plan),
        ],
    )


def _ts_constants(plan: _RequestPlan) -> str:
    lines = [f'const BASE_URL = "{_BASE_URL_PLACEHOLDER}";']
    if plan.needs_auth:
        lines.append(f'const CLIENT_ID = "{_CLIENT_ID_PLACEHOLDER}";')
        lines.append(f'const CLIENT_SECRET = "{_CLIENT_SECRET_PLACEHOLDER}";')
    return "\n".join(lines)


def _ts_path_param_vars(plan: _RequestPlan) -> str:
    return "\n".join(f'const {p.name} = "{p.placeholder}";' for p in plan.path_params)


def _ts_auth_header(plan: _RequestPlan) -> str:
    if not plan.needs_auth:
        return ""
    return 'const authHeader = "Basic " + btoa(`${CLIENT_ID}:${CLIENT_SECRET}`);'


def _ts_query_setup(plan: _RequestPlan) -> str:
    if not plan.query_params:
        return ""
    query_dict = {p.name: p.placeholder for p in plan.query_params}
    return f"const query = new URLSearchParams({json.dumps(query_dict, ensure_ascii=False)});"


def _ts_body(plan: _RequestPlan) -> str:
    match plan.body:
        case _MultipartBody():
            return 'const form = new FormData();\nform.append("file", file); // `file`: File or Blob à uploader'
        case _JsonBody(example=None):
            return "const body = {};"
        case _JsonBody(example=ex):
            return f"const body = {json.dumps(ex, indent=2, ensure_ascii=False)};"
        case _NoBody():
            return ""


def _ts_fetch_call(plan: _RequestPlan) -> str:
    options: list[str] = [f'method: "{plan.method.upper()}"']
    headers_block = _ts_headers_block(plan)
    if headers_block:
        options.append(headers_block)
    body_argument = _ts_body_argument(plan.body)
    if body_argument is not None:
        options.append(f"body: {body_argument}")

    options_text = textwrap.indent(",\n".join(options) + ",", _TS_INDENT)
    return "\n".join(
        [
            f"const response = await fetch({_ts_url_expression(plan)}, {{",
            options_text,
            "});",
            "if (!response.ok) throw new Error(`HTTP ${response.status}`);",
            "const data = await response.json();",
            "console.log(data);",
        ],
    )


def _ts_headers_block(plan: _RequestPlan) -> str:
    items: list[str] = []
    if plan.needs_auth:
        items.append('"Authorization": authHeader')
    if isinstance(plan.body, _JsonBody):
        items.append('"Content-Type": "application/json"')
    if not items:
        return ""
    inner = textwrap.indent(",\n".join(items), _TS_INDENT)
    return f"headers: {{\n{inner}\n}}"


def _ts_body_argument(body: _Body) -> str | None:
    match body:
        case _MultipartBody():
            return "form"
        case _JsonBody():
            return "JSON.stringify(body)"
        case _NoBody():
            return None


def _ts_url_expression(plan: _RequestPlan) -> str:
    path = plan.path
    for p in plan.path_params:
        path = path.replace(f"{{{p.name}}}", f"${{{p.name}}}")
    if plan.query_params:
        return f"`${{BASE_URL}}{path}?${{query.toString()}}`"
    return f"`${{BASE_URL}}{path}`"


# ── Registre des renderers ─────────────────────────────────────────────────

_Renderer = Callable[[_RequestPlan], str]
_RENDERERS: tuple[tuple[CodeSampleLang, str, _Renderer], ...] = (
    (CodeSampleLang.PYTHON, "Python (requests)", _render_python),
    (CodeSampleLang.TYPESCRIPT, "TypeScript (fetch)", _render_typescript),
)
