from __future__ import annotations

import ast
import fnmatch
import re
from pathlib import Path
from typing import Any

from .common import RunContext, normalized_relative, posix_relative, read_text_lossy, sha256_bytes, source_files, stable_id


REPORT_FRAGMENT = re.compile(r"(?:\.\./|\./)?reports/[A-Za-z0-9_./{}%:+-]+")
SHELL_ASSIGNMENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
SHELL_VARIABLE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


def _join(left: str, right: str) -> str:
    if not left:
        return normalized_relative(right)
    return normalized_relative(f"{left.rstrip('/')}/{right.lstrip('/')}")


def _path_value(value: str) -> str | None:
    value = value.strip().strip("'\"")
    if "/reports/" in value:
        value = "reports/" + value.split("/reports/", 1)[1]
    value = normalized_relative(value)
    if value == "reports" or value.startswith("reports/"):
        return value
    return None


class ExpressionResolver:
    def __init__(self, env: dict[str, str]):
        self.env = env

    def resolve(self, node: ast.AST | None) -> str | None:
        if node is None:
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            if node.id.endswith("REPORT_DIR"):
                return "reports"
            if node.id.endswith("PROJECT_ROOT"):
                return ""
            return None
        if isinstance(node, ast.Attribute):
            dotted = self._dotted(node)
            return self.env.get(dotted) or self.env.get(node.attr)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add)):
            left = self.resolve(node.left)
            right = self.resolve(node.right)
            if left is not None and right is not None:
                return _join(left, right) if isinstance(node.op, ast.Div) else f"{left}{right}"
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for item in node.values:
                if isinstance(item, ast.Constant):
                    parts.append(str(item.value))
                else:
                    parts.append("*")
            return "".join(parts)
        if isinstance(node, ast.Call):
            name = self.call_name(node.func)
            if name.endswith("strftime") or name.endswith("isoformat") or name in {"date", "datetime", "str"}:
                return "*"
            if name.endswith("Path") and node.args:
                return self.resolve(node.args[0])
            if name.endswith("joinpath"):
                base = self.resolve(node.func.value) if isinstance(node.func, ast.Attribute) else None
                pieces = [self.resolve(arg) for arg in node.args]
                if base is not None and all(piece is not None for piece in pieces):
                    result = base
                    for piece in pieces:
                        result = _join(result, str(piece))
                    return result
        return None

    @staticmethod
    def call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = ExpressionResolver.call_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""

    @staticmethod
    def _dotted(node: ast.Attribute) -> str:
        parts: list[str] = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))


def _report_matches(value: str | None, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if value is None:
        return []
    normalized = _path_value(value)
    if normalized is None:
        return []
    if "*" in normalized or "{" in normalized or "%" in normalized:
        pattern = normalized.replace("{", "*").replace("}", "*")
        pattern = re.sub(r"%[-_0-9A-Za-z]+", "*", pattern)
        while "**" in pattern:
            pattern = pattern.replace("**", "*")
        return [record for record in reports if fnmatch.fnmatch(record["relative_path"], pattern)]
    return [record for record in reports if record["relative_path"] == normalized]


def _reference(
    context: RunContext,
    report: dict[str, Any],
    source_path: str,
    line: int,
    excerpt: str,
    kind: str,
    direction: str,
    search_value: str,
) -> dict[str, Any]:
    excerpt = excerpt.strip()[:500]
    reference_id = stable_id(
        "structured-ref", report["report_id"], source_path, line, kind, direction, search_value
    )
    return {
        "reference_id": reference_id,
        "report_id": report["report_id"],
        "report_path": report["relative_path"],
        "source_path": source_path,
        "line": line,
        "excerpt": excerpt,
        "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "reference_kind": kind,
        "direction": direction,
        "search_value": search_value,
        "scanner": "STRUCTURED",
        "scanner_version": context.config["structured_scanner_version"],
    }


def _module_names(path: Path, root: Path) -> set[str]:
    relative = path.relative_to(root).with_suffix("")
    dotted = ".".join(relative.parts)
    names = {dotted, path.stem}
    if dotted.startswith("src."):
        names.add(dotted[4:])
    if dotted.startswith("scripts."):
        names.add(dotted[8:])
    return names


def _collect_python_exports(context: RunContext, python_files: list[Path]) -> dict[str, dict[str, str]]:
    exports: dict[str, dict[str, str]] = {}
    for path in python_files:
        try:
            tree = ast.parse(read_text_lossy(path), filename=str(path))
        except SyntaxError:
            continue
        env: dict[str, str] = {"PROJECT_ROOT": "", "REPORT_DIR": "reports"}
        resolver = ExpressionResolver(env)
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value_node = node.value
                value = resolver.resolve(value_node)
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and value is not None:
                        env[target.id] = value
        for name in _module_names(path, context.root):
            exports[name] = dict(env)
    return exports


def _scan_python(
    context: RunContext,
    path: Path,
    reports: list[dict[str, Any]],
    exports: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    text = read_text_lossy(path)
    lines = text.splitlines()
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []
    env: dict[str, str] = {"PROJECT_ROOT": "", "REPORT_DIR": "reports"}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in exports:
            for alias in node.names:
                imported = exports[node.module].get(alias.name)
                if imported is not None:
                    env[alias.asname or alias.name] = imported
    references: list[dict[str, Any]] = []
    source_path = posix_relative(path, context.root)

    def add(value: str | None, node: ast.AST, kind: str, direction: str) -> None:
        for report in _report_matches(value, reports):
            line = getattr(node, "lineno", 0)
            excerpt = lines[line - 1] if 0 < line <= len(lines) else ""
            references.append(_reference(context, report, source_path, line, excerpt, kind, direction, value or ""))

    def scoped_nodes(statements: list[ast.stmt]) -> list[ast.AST]:
        output: list[ast.AST] = []

        def visit(node: ast.AST) -> None:
            output.append(node)
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    continue
                visit(child)

        for statement in statements:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            visit(statement)
        return output

    def scan_scope(
        statements: list[ast.stmt],
        inherited_env: dict[str, str],
        class_name: str | None = None,
        class_attrs: dict[str, str] | None = None,
        recurse_functions: bool = True,
    ) -> dict[str, str]:
        scope_env = dict(inherited_env)
        if class_attrs:
            for name, value in class_attrs.items():
                scope_env[f"self.{name}"] = value
                scope_env[f"cls.{name}"] = value
                if class_name:
                    scope_env[f"{class_name}.{name}"] = value
        resolver = ExpressionResolver(scope_env)
        nodes = scoped_nodes(statements)
        for node in nodes:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = resolver.resolve(node.value)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                target_name = None
                if isinstance(target, ast.Name):
                    target_name = target.id
                elif isinstance(target, ast.Attribute):
                    target_name = resolver._dotted(target)
                if target_name and value is not None:
                    scope_env[target_name] = value
                    add(value, node, "PYTHON_PATH_BINDING", "DECLARATION")
        for node in nodes:
            if not isinstance(node, ast.Call):
                continue
            call_name = resolver.call_name(node.func)
            short_name = call_name.rsplit(".", 1)[-1]
            producer_values: list[str | None] = []
            consumer_values: list[str | None] = []
            if short_name in {"write_text", "write_bytes"} and isinstance(node.func, ast.Attribute):
                producer_values.append(resolver.resolve(node.func.value))
            elif short_name in {"to_csv", "to_json", "to_parquet", "save", "dump"}:
                if isinstance(node.func, ast.Attribute) and short_name == "save":
                    producer_values.append(resolver.resolve(node.func.value))
                if node.args:
                    producer_values.append(resolver.resolve(node.args[0]))
            elif short_name in {"_write_json", "write_json", "write_report"} and node.args:
                producer_values.append(resolver.resolve(node.args[0]))
            elif short_name == "write_payload":
                producer_values.extend(resolver.resolve(arg) for arg in node.args[:3])
            elif short_name == "open":
                target = resolver.resolve(node.args[0]) if node.args else (
                    resolver.resolve(node.func.value) if isinstance(node.func, ast.Attribute) else None
                )
                mode = resolver.resolve(node.args[1]) if len(node.args) > 1 else "r"
                if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
                    producer_values.append(target)
                else:
                    consumer_values.append(target)
            if short_name in {"read_text", "read_bytes"} and isinstance(node.func, ast.Attribute):
                consumer_values.append(resolver.resolve(node.func.value))
            elif short_name in {"read_csv", "read_json", "read_parquet", "load"} and node.args:
                consumer_values.append(resolver.resolve(node.args[0]))
            elif short_name in {"exists", "stat", "is_file"} and isinstance(node.func, ast.Attribute):
                consumer_values.append(resolver.resolve(node.func.value))
            for value in producer_values:
                add(value, node, "PYTHON_WRITE", "PRODUCER")
            for value in consumer_values:
                add(value, node, "PYTHON_READ", "CONSUMER")
        for statement in statements:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and recurse_functions:
                scan_scope(statement.body, scope_env, class_name, class_attrs)
            elif isinstance(statement, ast.ClassDef):
                class_env = scan_scope(statement.body, scope_env, recurse_functions=False)
                attrs = {key: value for key, value in class_env.items() if key not in scope_env}
                for member in statement.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        scan_scope(member.body, scope_env, statement.name, attrs)
        return scope_env

    scan_scope(tree.body, env)
    return references


def _expand_shell_value(value: str, env: dict[str, str]) -> str:
    value = value.strip().strip("'\"")
    for _ in range(4):
        expanded = SHELL_VARIABLE.sub(lambda match: env.get(match.group(1), "*"), value)
        if expanded == value:
            break
        value = expanded
    return value.replace("$PROJECT_ROOT/", "").replace("${PROJECT_ROOT}/", "")


def _scan_shell(context: RunContext, path: Path, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = read_text_lossy(path).splitlines()
    env = {"PROJECT_ROOT": "", "REPORT_DIR": "reports"}
    bindings: dict[str, str] = {}
    references: list[dict[str, Any]] = []
    source_path = posix_relative(path, context.root)
    for index, line in enumerate(lines, 1):
        match = SHELL_ASSIGNMENT.match(line)
        if match:
            name, raw_value = match.groups()
            value = _expand_shell_value(raw_value, {**env, **bindings})
            env[name] = value
            bindings[name] = value
            for report in _report_matches(value, reports):
                references.append(_reference(context, report, source_path, index, line, "SHELL_PATH_BINDING", "DECLARATION", value))
        for name, value in sorted(bindings.items()):
            if not re.search(rf"\$\{{?{re.escape(name)}\}}?", line) or match and match.group(1) == name:
                continue
            output_cue = bool(re.search(r"(?:>>?|\btee\b|--(?:output|out|status-json|report|dest(?:ination)?)\b)", line))
            input_cue = bool(re.search(r"(?:--(?:input|source|config)\b|\bcat\b|\bsource\b)", line))
            direction = "PRODUCER" if output_cue else "CONSUMER" if input_cue else "REFERENCE"
            kind = "SHELL_OUTPUT" if output_cue else "SHELL_INPUT" if input_cue else "SHELL_ARGUMENT"
            for report in _report_matches(value, reports):
                references.append(_reference(context, report, source_path, index, line, kind, direction, value))
    return references


def _scan_config_or_frontend(context: RunContext, path: Path, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    source_path = posix_relative(path, context.root)
    for index, line in enumerate(read_text_lossy(path).splitlines(), 1):
        candidates = set(REPORT_FRAGMENT.findall(line))
        for report in reports:
            if report["relative_path"] in line or report["filename"] in line:
                candidates.add(report["relative_path"])
        for candidate in sorted(candidates):
            direction = "CONSUMER" if re.search(r"fetch\s*\(|import\s|href=|read", line, re.I) else "REFERENCE"
            kind = "FRONTEND_RUNTIME_REFERENCE" if direction == "CONSUMER" else "CONFIG_REFERENCE"
            for report in _report_matches(candidate, reports):
                references.append(_reference(context, report, source_path, index, line, kind, direction, candidate))
    return references


def scan_structured_references(context: RunContext, reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    files = source_files(context)
    python_files = [path for path in files if path.suffix.lower() == ".py"]
    exports = _collect_python_exports(context, python_files)
    records: list[dict[str, Any]] = []
    for path in files:
        suffix = path.suffix.lower()
        if suffix == ".py":
            records.extend(_scan_python(context, path, reports, exports))
        elif suffix == ".sh":
            records.extend(_scan_shell(context, path, reports))
        else:
            records.extend(_scan_config_or_frontend(context, path, reports))
    unique = {record["reference_id"]: record for record in records}
    return [unique[key] for key in sorted(unique)]
