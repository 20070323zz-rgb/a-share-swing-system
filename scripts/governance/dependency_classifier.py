"""Structured report-reference classification for Reports Governance Phase A.

Python is parsed with ``ast``.  Shell, frontend, HTML and documentation files
use source-aware parsers with deliberately narrow operation rules.  A path
mention alone is never promoted to a producer or runtime read.
"""

from __future__ import annotations

import ast
import hashlib
import re
import shlex
from dataclasses import dataclass
from pathlib import Path


GENERATOR_VERSION = "2.2.0"
REPORT_EXTENSIONS = (".csv", ".html", ".json", ".md", ".parquet", ".txt", ".yaml", ".yml")
EXPLICIT_REPORT_RE = re.compile(r"(?<![A-Za-z0-9_.-])/?(reports/[A-Za-z0-9_./*?{}\[\]$-]+)")
SHELL_REPORT_DIR_RE = re.compile(
    r"\$(?:\{)?REPORTS?_DIR(?:\})?/([^\"'\s]+(?:\.csv|\.html|\.json|\.md|\.parquet|\.txt|\.yaml|\.yml))"
)
REPORT_DIR_EXPR_RE = re.compile(
    r"(?:REPORTS?_DIR|reports?_dir|Path\([\"']reports[\"']\))"
    r"(?P<tail>(?:\s*/\s*[furbFURB]*[\"'][^\"']+[\"'])+)"
)
QUOTED_RE = re.compile(r"[furbFURB]*[\"']([^\"']+)[\"']")

PYTHON_PRODUCER_METHODS = {
    "write_text",
    "write_bytes",
    "write_csv",
    "write_json",
    "to_csv",
    "to_json",
    "to_parquet",
    "dump",
    "safe_dump",
    "writerow",
    "writerows",
}
PYTHON_CONSUMER_METHODS = {
    "read_text",
    "read_bytes",
    "read_csv",
    "read_json",
    "read_parquet",
    "load",
    "safe_load",
    "read_json_file",
    "read_csv_rows",
    "tail_text",
    "_read_json",
    "_read_csv",
    "_read_text",
    "_mtime",
}
PYTHON_ATOMIC_METHODS = {"replace", "rename"}
PYTHON_COPY_METHODS = {"copy", "copy2", "move"}


@dataclass(frozen=True)
class Reference:
    target: str
    resolution: str
    dynamic_path_pattern: str = ""
    pattern_kind: str = ""
    binding_id: str = ""
    binding_name: str = ""
    binding_version: int = 0
    binding_scope_id: str = ""
    binding_origin_scope_id: str = ""
    binding_confidence: str = ""


@dataclass
class Binding:
    binding_id: str
    name: str
    version: int
    scope_id: str
    values: list[Reference]
    confidence: str = "HIGH"


@dataclass
class ScopeFrame:
    scope_id: str
    scope_type: str
    qualified_name: str
    parent: "ScopeFrame | None"
    bindings: dict[str, Binding]


def _clean_reference(raw: str) -> str:
    value = raw.lstrip("/").rstrip(".,;:)")
    while "//" in value:
        value = value.replace("//", "/")
    return value


def _is_dynamic(target: str) -> bool:
    return any(token in target for token in ("*", "?", "{", "}", "[", "]", "$"))


def extract_report_references(text: str) -> list[tuple[str, str]]:
    """Extract normalized report targets without inferring read/write semantics."""

    found: dict[str, str] = {}
    for match in EXPLICIT_REPORT_RE.finditer(text):
        target = _clean_reference(match.group(1))
        if target != "reports/":
            found[target] = "DYNAMIC" if _is_dynamic(target) else "STATIC"
    for match in SHELL_REPORT_DIR_RE.finditer(text):
        target = _clean_reference("reports/" + match.group(1).strip("/"))
        found[target] = "DYNAMIC" if _is_dynamic(target) else "STATIC_COMPUTED"
    for match in REPORT_DIR_EXPR_RE.finditer(text):
        segments = [
            item.strip("/")
            for item in QUOTED_RE.findall(match.group("tail"))
            if item.strip("/") and item not in {"r", "w", "a", "x", "rb", "wb", "utf-8", "reports"}
        ]
        if segments and segments[-1].endswith(REPORT_EXTENSIONS):
            target = _clean_reference("reports/" + "/".join(segments))
            found[target] = "DYNAMIC" if _is_dynamic(target) else "STATIC_COMPUTED"
    return sorted(found.items())


def _normalized_excerpt(excerpt: str) -> str:
    return " ".join(excerpt.strip().split())


def _impact(reference_type: str) -> str:
    if reference_type in {"APP_RUNTIME_READ", "DASHBOARD_RUNTIME_READ"}:
        return "CRITICAL"
    if reference_type in {"PRODUCER_WRITE", "CONSUMER_READ", "FILE_COPY_SOURCE", "FILE_MOVE_SOURCE"}:
        return "HIGH"
    if reference_type in {"TEST_REFERENCE", "STATE_INDEX_REFERENCE", "DYNAMIC_PATH_PATTERN"}:
        return "MEDIUM"
    return "LOW"


def _record(
    *,
    source_file: str,
    line_start: int,
    line_end: int,
    target: str,
    resolution: str,
    reference_type: str,
    direction: str,
    parser_type: str,
    confidence: str,
    excerpt: str,
    source_tree_commit: str,
    scope: ScopeFrame | None = None,
    reference: Reference | None = None,
) -> dict:
    normalized = _normalized_excerpt(excerpt)
    excerpt_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    identity = "\n".join((source_file, target, reference_type, direction, normalized))
    reference_id = "ref_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    dynamic = resolution == "DYNAMIC"
    compatibility_actor = (
        "PRODUCER"
        if direction in {"PRODUCER", "WRITE"}
        else "CONSUMER"
        if direction in {"CONSUMER", "READ", "MOVE_SOURCE"}
        else direction
    )
    return {
        "reference_id": reference_id,
        "source_file": source_file,
        "source_line_start": line_start,
        "source_line_end": line_end,
        "normalized_target": target,
        "reference_type": reference_type,
        "direction": direction,
        "parser_type": parser_type,
        "confidence": confidence,
        "source_excerpt_hash": excerpt_hash,
        "generator_version": GENERATOR_VERSION,
        "source_tree_commit": source_tree_commit,
        "scope_id": scope.scope_id if scope else "",
        "scope_type": scope.scope_type if scope else "",
        "scope_qualified_name": scope.qualified_name if scope else "",
        "binding_id": reference.binding_id if reference else "",
        "binding_name": reference.binding_name if reference else "",
        "binding_version": reference.binding_version if reference else 0,
        "binding_scope_id": reference.binding_scope_id if reference else "",
        "binding_origin_scope_id": reference.binding_origin_scope_id if reference else "",
        "binding_confidence": reference.binding_confidence if reference else "",
        "dynamic_path_pattern": reference.dynamic_path_pattern if reference else "",
        "dynamic_pattern_kind": reference.pattern_kind if reference else "",
        "producer_entrypoint": source_file if reference_type == "PRODUCER_WRITE" else "",
        # Compatibility fields retained for Catalog V1 readers.
        "source_line": line_start,
        "referenced_report_path": target,
        "consumer_or_producer": compatibility_actor,
        "static_or_dynamic": "DYNAMIC" if dynamic else "STATIC",
        "migration_impact": _impact(reference_type),
        "notes": (
            "Dynamic pattern retained without fabricating a concrete target."
            if dynamic
            else "Structured source classification; exact target."
        ),
    }


SHELL_CONTROL_TOKENS = {"&&", "||", ";", "|"}
SHELL_VARIABLE_RE = re.compile(r"^\$(?:\{)?([A-Za-z_][A-Za-z0-9_]*)(?:\})?$")


def _shell_tokens(line: str) -> list[str]:
    lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return list(lexer)


def _shell_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SHELL_CONTROL_TOKENS:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def _shell_token_references(token: str) -> list[Reference]:
    direct = [Reference(*item) for item in extract_report_references(token)]
    if direct:
        return direct
    variable = SHELL_VARIABLE_RE.fullmatch(token)
    if variable and variable.group(1).upper().startswith(("REPORT_", "REPORTS_")):
        name = variable.group(1)
        return [Reference(f"reports/${{{name}}}", "DYNAMIC")]
    return []


def _report_directory_prefix(token: str) -> str | None:
    value = token.removeprefix("./").rstrip()
    if value in {"reports", "reports/"}:
        return "reports/"
    if value.startswith("reports/") and (value.endswith("/") or not Path(value).suffix):
        return value.rstrip("/") + "/"
    if value in {"$REPORT_DIR", "${REPORT_DIR}", "$REPORTS_DIR", "${REPORTS_DIR}"}:
        return "reports/"
    return None


def _source_basename_pattern(token: str) -> str | None:
    value = token.rstrip("/")
    if not value:
        return None
    variable = SHELL_VARIABLE_RE.fullmatch(value)
    if variable:
        return None
    name = value.rsplit("/", 1)[-1]
    return name if name and name not in {".", ".."} else None


def _parse_copy_move_operands(segment: list[str], command_index: int) -> tuple[list[str], str, bool] | None:
    operands: list[str] = []
    target_directory: str | None = None
    options_done = False
    index = command_index + 1
    while index < len(segment):
        token = segment[index]
        if not options_done and token == "--":
            options_done = True
        elif not options_done and token in {"-t", "--target-directory"}:
            index += 1
            if index >= len(segment):
                return None
            target_directory = segment[index]
        elif not options_done and token.startswith("--target-directory="):
            target_directory = token.split("=", 1)[1]
        elif not options_done and token.startswith("-t") and len(token) > 2:
            target_directory = token[2:]
        elif not options_done and token.startswith("-") and token != "-":
            pass
        else:
            operands.append(token)
        index += 1

    if target_directory is not None:
        return (operands, target_directory, True) if operands else None
    if len(operands) < 2:
        return None
    sources = operands[:-1]
    destination = operands[-1]
    return sources, destination, len(sources) > 1 or destination.endswith("/")


def _shell_copy_move_rows(
    source_file: str,
    line: str,
    line_number: int,
    source_tree_commit: str,
) -> list[dict] | None:
    try:
        segments = _shell_segments(_shell_tokens(line))
    except ValueError:
        return None

    found_command = False
    rows: list[dict] = []
    for segment in segments:
        command_index = next(
            (index for index, token in enumerate(segment) if Path(token).name in {"cp", "mv"}),
            None,
        )
        if command_index is None:
            continue
        found_command = True
        operation = Path(segment[command_index]).name
        parsed = _parse_copy_move_operands(segment, command_index)
        if parsed is None:
            continue
        sources, destination, destination_is_directory = parsed
        source_direction = "READ" if operation == "cp" else "MOVE_SOURCE"
        source_type = "FILE_COPY_SOURCE" if operation == "cp" else "FILE_MOVE_SOURCE"

        for source in sources:
            for ref in _shell_token_references(source):
                dynamic = ref.resolution == "DYNAMIC"
                rows.append(
                    _record(
                        source_file=source_file,
                        line_start=line_number,
                        line_end=line_number,
                        target=ref.target,
                        resolution=ref.resolution,
                        reference_type="DYNAMIC_PATH_PATTERN" if dynamic else source_type,
                        direction=source_direction,
                        parser_type="SHELL",
                        confidence="LOW" if dynamic else "MEDIUM" if ref.resolution == "STATIC_COMPUTED" else "HIGH",
                        excerpt=line,
                        source_tree_commit=source_tree_commit,
                    )
                )

        destination_prefix = _report_directory_prefix(destination) if destination_is_directory else None
        destination_refs = [] if destination_prefix else _shell_token_references(destination)
        for ref in destination_refs:
            dynamic = ref.resolution == "DYNAMIC"
            rows.append(
                _record(
                    source_file=source_file,
                    line_start=line_number,
                    line_end=line_number,
                    target=ref.target,
                    resolution=ref.resolution,
                    reference_type="DYNAMIC_PATH_PATTERN" if dynamic else "PRODUCER_WRITE",
                    direction="WRITE",
                    parser_type="SHELL",
                    confidence="LOW" if dynamic else "MEDIUM" if ref.resolution == "STATIC_COMPUTED" else "HIGH",
                    excerpt=line,
                    source_tree_commit=source_tree_commit,
                )
            )

        if destination_prefix:
            for source in sources:
                basename = _source_basename_pattern(source)
                target = destination_prefix + (basename or "*")
                dynamic = _is_dynamic(target) or basename is None
                rows.append(
                    _record(
                        source_file=source_file,
                        line_start=line_number,
                        line_end=line_number,
                        target=target,
                        resolution="DYNAMIC" if dynamic else "STATIC_COMPUTED",
                        reference_type="DYNAMIC_PATH_PATTERN" if dynamic else "PRODUCER_WRITE",
                        direction="WRITE",
                        parser_type="SHELL",
                        confidence="LOW" if dynamic else "MEDIUM",
                        excerpt=line,
                        source_tree_commit=source_tree_commit,
                    )
                )
    return rows if found_command else None


def _placeholder(node: ast.AST, format_spec: str = "") -> tuple[str, str, str]:
    raw_name = ast.unparse(node) if hasattr(ast, "unparse") else "expr"
    name = raw_name.rsplit(".", 1)[-1].lower()
    if any(token in format_spec for token in ("%H", "%M", "%S")) or any(
        token in name for token in ("timestamp", "datetime", "date_time")
    ):
        return "{" + raw_name + "}", "<TIMESTAMP>", "TIMESTAMP_TEMPLATE"
    if any(token in format_spec for token in ("%Y", "%y", "%m", "%d")) or any(
        token in name for token in ("date", "day", "week_end")
    ):
        return "{" + raw_name + "}", "<DATE>", "DATE_TEMPLATE"
    if "run_id" in name or name == "runid":
        return "{" + raw_name + "}", "<RUN_ID>", "RUN_ID_TEMPLATE"
    return "{" + raw_name + "}", "<DYNAMIC>", "UNKNOWN_DYNAMIC"


def _merge_pattern_kind(kinds: list[str]) -> str:
    nonempty = {kind for kind in kinds if kind}
    if not nonempty:
        return ""
    return next(iter(nonempty)) if len(nonempty) == 1 else "MIXED_TEMPLATE"


def _derived_reference(raw: str, pattern: str, parts: list[Reference]) -> Reference:
    metadata = next((part for part in parts if part.binding_id), None)
    kind = _merge_pattern_kind([part.pattern_kind for part in parts])
    dynamic = raw != pattern or "{" in raw or "<" in pattern
    return Reference(
        target=_clean_reference(raw),
        resolution="DYNAMIC" if dynamic else "STATIC_COMPUTED",
        dynamic_path_pattern=_clean_reference(pattern) if dynamic else "",
        pattern_kind=kind or ("UNKNOWN_DYNAMIC" if dynamic else ""),
        binding_id=metadata.binding_id if metadata else "",
        binding_name=metadata.binding_name if metadata else "",
        binding_version=metadata.binding_version if metadata else 0,
        binding_scope_id=metadata.binding_scope_id if metadata else "",
        binding_origin_scope_id=metadata.binding_origin_scope_id if metadata else "",
        binding_confidence=metadata.binding_confidence if metadata else "",
    )


def _decorate_binding(ref: Reference, binding: Binding, current_scope_id: str) -> Reference:
    return Reference(
        target=ref.target,
        resolution=ref.resolution,
        dynamic_path_pattern=ref.dynamic_path_pattern,
        pattern_kind=ref.pattern_kind,
        binding_id=binding.binding_id,
        binding_name=binding.name,
        binding_version=binding.version,
        binding_scope_id=current_scope_id,
        binding_origin_scope_id=binding.scope_id,
        binding_confidence=binding.confidence,
    )


def _lookup_binding(frame: ScopeFrame, name: str) -> list[Reference]:
    current: ScopeFrame | None = frame
    while current is not None:
        if name in current.bindings:
            binding = current.bindings[name]
            return [_decorate_binding(ref, binding, frame.scope_id) for ref in binding.values]
        current = current.parent
    if name.upper() in {"REPORT_DIR", "REPORTS_DIR"}:
        return [Reference("reports", "STATIC_COMPUTED")]
    return []


def _attribute_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _attribute_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _combine_values(left: list[Reference], right: list[Reference], separator: str) -> list[Reference]:
    result: list[Reference] = []
    for lhs in left:
        for rhs in right:
            raw = lhs.target.rstrip("/") + separator + rhs.target.lstrip("/")
            lhs_pattern = lhs.dynamic_path_pattern or lhs.target
            rhs_pattern = rhs.dynamic_path_pattern or rhs.target
            pattern = lhs_pattern.rstrip("/") + separator + rhs_pattern.lstrip("/")
            result.append(_derived_reference(raw, pattern, [lhs, rhs]))
    return result


def _expr_references(node: ast.AST | None, frame: ScopeFrame) -> list[Reference]:
    """Resolve path-like expressions in the current lexical environment."""

    if node is None:
        return []
    if isinstance(node, ast.Name):
        return _lookup_binding(frame, node.id)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, int, float)):
            value = str(node.value)
            dynamic = _is_dynamic(value)
            pattern = value
            kind = "UNKNOWN_DYNAMIC" if dynamic else ""
            return [Reference(value, "DYNAMIC" if dynamic else "STATIC_COMPUTED", pattern if dynamic else "", kind)]
        return []
    if isinstance(node, ast.JoinedStr):
        values = [Reference("", "STATIC_COMPUTED")]
        for part in node.values:
            if isinstance(part, ast.Constant):
                segment = [Reference(str(part.value), "STATIC_COMPUTED")]
            elif isinstance(part, ast.FormattedValue):
                spec = ""
                if part.format_spec is not None:
                    spec = "".join(
                        str(value.value) for value in part.format_spec.values if isinstance(value, ast.Constant)
                    )
                raw, pattern, kind = _placeholder(part.value, spec)
                segment = [Reference(raw, "DYNAMIC", pattern, kind)]
            else:
                segment = []
            values = _combine_values(values, segment, "")
        return values
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add)):
        return _combine_values(
            _expr_references(node.left, frame),
            _expr_references(node.right, frame),
            "/" if isinstance(node.op, ast.Div) else "",
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        left = _expr_references(node.left, frame)
        values = node.right.elts if isinstance(node.right, (ast.Tuple, ast.List)) else [node.right]
        result: list[Reference] = []
        for base in left:
            raw = base.target
            pattern = base.dynamic_path_pattern or base.target
            kinds = [base.pattern_kind]
            for value in values:
                placeholder_raw, placeholder_pattern, kind = _placeholder(value)
                raw = re.sub(r"%[-+0-9.#]*[a-zA-Z]", placeholder_raw, raw, count=1)
                pattern = re.sub(r"%[-+0-9.#]*[a-zA-Z]", placeholder_pattern, pattern, count=1)
                kinds.append(kind)
            result.append(_derived_reference(raw, pattern, [base, Reference("", "DYNAMIC", pattern, _merge_pattern_kind(kinds))]))
        return result
    if isinstance(node, ast.Call):
        call_name = _attribute_name(node.func)
        method = call_name.rsplit(".", 1)[-1]
        receiver = _expr_references(node.func.value, frame) if isinstance(node.func, ast.Attribute) else []
        if method in {"Path", "PurePath", "PurePosixPath"} and node.args:
            return _expr_references(node.args[0], frame)
        if call_name in {"os.path.join", "posixpath.join", "ntpath.join"} or method == "joinpath":
            values = receiver if method == "joinpath" else [Reference("", "STATIC_COMPUTED")]
            for arg in node.args:
                values = _combine_values(values, _expr_references(arg, frame), "/")
            return values
        if method == "format" and receiver:
            result: list[Reference] = []
            positional = list(node.args)
            keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
            for base in receiver:
                raw = base.target
                pattern = base.dynamic_path_pattern or base.target
                kinds = [base.pattern_kind]
                fields = list(re.finditer(r"\{([^{}]*)\}", raw))
                for index, match in enumerate(fields):
                    field = match.group(1).split(":", 1)[0]
                    value_node = keywords.get(field)
                    if value_node is None and index < len(positional):
                        value_node = positional[index]
                    if value_node is None:
                        continue
                    raw_token, pattern_token, kind = _placeholder(value_node)
                    raw = raw.replace(match.group(0), raw_token, 1)
                    pattern = re.sub(r"\{[^{}]*\}", pattern_token, pattern, count=1)
                    kinds.append(kind)
                result.append(_derived_reference(raw, pattern, [base, Reference("", "DYNAMIC", pattern, _merge_pattern_kind(kinds))]))
            return result
        if method == "with_name" and receiver and node.args:
            names = _expr_references(node.args[0], frame)
            result: list[Reference] = []
            for base in receiver:
                parent = base.target.rsplit("/", 1)[0] if "/" in base.target else ""
                parent_pattern = (base.dynamic_path_pattern or base.target).rsplit("/", 1)[0] if "/" in (base.dynamic_path_pattern or base.target) else ""
                for name in names:
                    result.append(_derived_reference(f"{parent}/{name.target}", f"{parent_pattern}/{name.dynamic_path_pattern or name.target}", [base, name]))
            return result
        if method == "with_suffix" and receiver and node.args:
            suffixes = _expr_references(node.args[0], frame)
            result: list[Reference] = []
            for base in receiver:
                for suffix in suffixes:
                    raw = re.sub(r"\.[^./]+$", "", base.target) + suffix.target
                    pattern = re.sub(r"\.[^./]+$", "", base.dynamic_path_pattern or base.target) + (suffix.dynamic_path_pattern or suffix.target)
                    result.append(_derived_reference(raw, pattern, [base, suffix]))
            return result
        if method == "strftime" and receiver and node.args:
            formats = _expr_references(node.args[0], frame)
            result = []
            for fmt in formats:
                raw, pattern, kind = _placeholder(node.func.value, fmt.target)
                result.append(Reference(raw, "DYNAMIC", pattern, kind))
            return result
        direct = [Reference(*item) for item in extract_report_references(ast.unparse(node))]
        if direct:
            return direct
        result: list[Reference] = []
        for item in node.args:
            result.extend(_expr_references(item, frame))
        return result
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        result: list[Reference] = []
        for item in node.elts:
            result.extend(_expr_references(item, frame))
        return result
    if isinstance(node, ast.Dict):
        result: list[Reference] = []
        for item in [*node.keys, *node.values]:
            result.extend(_expr_references(item, frame))
        return result
    direct = [Reference(*item) for item in extract_report_references(ast.unparse(node))]
    return direct


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _call_receiver(call: ast.Call, frame: ScopeFrame) -> list[Reference]:
    return _expr_references(call.func.value, frame) if isinstance(call.func, ast.Attribute) else []


def _runtime_read_type(source_file: str) -> str:
    if source_file.startswith(("app/backend/", "app/frontend/")):
        return "APP_RUNTIME_READ"
    if source_file.startswith("dashboard/"):
        return "DASHBOARD_RUNTIME_READ"
    return "CONSUMER_READ"


class _PythonAnalyzer:
    def __init__(self, source_file: str, text: str, source_tree_commit: str, tree: ast.Module):
        self.source_file = source_file
        self.lines = text.splitlines()
        self.source_tree_commit = source_tree_commit
        self.rows: list[dict] = []
        self.used: set[tuple[int, str]] = set()
        self.tree = tree

    def _scope(self, node: ast.AST, scope_type: str, name: str, parent: ScopeFrame | None) -> ScopeFrame:
        qualified = name if parent is None or parent.qualified_name == "<module>" else f"{parent.qualified_name}.{name}"
        identity = f"{self.source_file}:{scope_type}:{qualified}:{getattr(node, 'lineno', 1)}:{getattr(node, 'end_lineno', len(self.lines))}"
        return ScopeFrame("scope_" + hashlib.sha256(identity.encode()).hexdigest()[:16], scope_type, qualified, parent, {})

    def _bind(self, frame: ScopeFrame, name: str, values: list[Reference], node: ast.AST, confidence: str = "HIGH") -> None:
        previous = frame.bindings.get(name)
        version = previous.version + 1 if previous else 1
        signature = "|".join(f"{value.target}:{value.dynamic_path_pattern}" for value in values)
        identity = f"{frame.scope_id}:{name}:{version}:{getattr(node, 'lineno', 0)}:{signature}"
        frame.bindings[name] = Binding(
            "binding_" + hashlib.sha256(identity.encode()).hexdigest()[:16],
            name,
            version,
            frame.scope_id,
            values,
            confidence,
        )

    def _bind_target(self, frame: ScopeFrame, target: ast.AST, values: list[Reference], node: ast.AST, confidence: str = "HIGH") -> None:
        if isinstance(target, ast.Name):
            self._bind(frame, target.id, values, node, confidence)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self._bind_target(frame, element, [], node, confidence)

    def _emit_call(self, call: ast.Call, frame: ScopeFrame) -> None:
        name = _call_name(call)
        operations: list[tuple[list[Reference], str]] = []
        if name == "open":
            refs = _expr_references(call.args[0], frame) if call.args else []
            mode = "r"
            if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
                mode = str(call.args[1].value)
            for keyword in call.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = str(keyword.value.value)
            operations.append((refs, "PRODUCER" if any(flag in mode for flag in "wax+") else "CONSUMER"))
        elif name in PYTHON_PRODUCER_METHODS:
            refs = _call_receiver(call, frame)
            if name in {"to_csv", "to_json", "to_parquet", "write_csv", "write_json"} and call.args:
                refs = _expr_references(call.args[0], frame)
            elif name in {"dump", "safe_dump"} and len(call.args) > 1:
                refs = []
                for arg in call.args[1:]:
                    refs.extend(_expr_references(arg, frame))
            operations.append((refs, "PRODUCER"))
        elif name in PYTHON_CONSUMER_METHODS:
            refs = _call_receiver(call, frame)
            for arg in call.args:
                refs.extend(_expr_references(arg, frame))
            operations.append((refs, "CONSUMER"))
        elif name in PYTHON_COPY_METHODS | PYTHON_ATOMIC_METHODS:
            args = list(call.args)
            receiver = _call_receiver(call, frame)
            module_call = _attribute_name(call.func).rsplit(".", 1)[0] in {"os", "shutil"}
            if module_call and len(args) >= 2:
                operations.append((_expr_references(args[0], frame), "CONSUMER"))
                operations.append((_expr_references(args[1], frame), "PRODUCER"))
            elif isinstance(call.func, ast.Attribute) and args:
                if receiver:
                    operations.append((receiver, "CONSUMER"))
                operations.append((_expr_references(args[0], frame), "PRODUCER"))
            elif len(args) >= 2:
                operations.append((_expr_references(args[0], frame), "CONSUMER"))
                operations.append((_expr_references(args[1], frame), "PRODUCER"))
        elif name in {"fetch", "axios"}:
            refs: list[Reference] = []
            for arg in call.args:
                refs.extend(_expr_references(arg, frame))
            operations.append((refs, "CONSUMER"))

        end_lineno = getattr(call, "end_lineno", call.lineno)
        excerpt = "\n".join(self.lines[call.lineno - 1 : end_lineno])
        for refs, direction in operations:
            for ref in refs:
                if not ref.target.startswith("reports/") or not ref.target.endswith(REPORT_EXTENSIONS):
                    continue
                reference_type = (
                    "TEST_REFERENCE"
                    if self.source_file.startswith("tests/")
                    else "PRODUCER_WRITE"
                    if direction == "PRODUCER"
                    else _runtime_read_type(self.source_file)
                )
                confidence = "MEDIUM" if ref.resolution == "DYNAMIC" and ref.pattern_kind != "UNKNOWN_DYNAMIC" else "LOW" if ref.resolution == "DYNAMIC" else "HIGH"
                emitted_direction = "WRITE" if direction == "PRODUCER" and ref.resolution == "DYNAMIC" else direction
                self.rows.append(
                    _record(
                        source_file=self.source_file,
                        line_start=call.lineno,
                        line_end=end_lineno,
                        target=ref.target,
                        resolution=ref.resolution,
                        reference_type=reference_type,
                        direction=emitted_direction,
                        parser_type="PYTHON_AST",
                        confidence=confidence,
                        excerpt=excerpt,
                        source_tree_commit=self.source_tree_commit,
                        scope=frame,
                        reference=ref,
                    )
                )
                self.used.add((call.lineno, ref.target))

    def _process_expr(self, node: ast.AST | None, frame: ScopeFrame) -> None:
        if node is None:
            return
        if isinstance(node, ast.Lambda):
            child = self._scope(node, "LAMBDA", f"<lambda>@{node.lineno}", frame)
            for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
                self._bind(child, arg.arg, [], arg)
            self._process_expr(node.body, child)
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            child = self._scope(node, "COMPREHENSION", f"<{type(node).__name__.lower()}>@{node.lineno}", frame)
            for generator in node.generators:
                self._process_expr(generator.iter, child)
                self._bind_target(child, generator.target, [], generator)
                for condition in generator.ifs:
                    self._process_expr(condition, child)
            if isinstance(node, ast.DictComp):
                self._process_expr(node.key, child)
                self._process_expr(node.value, child)
            else:
                self._process_expr(node.elt, child)
            return
        if isinstance(node, ast.NamedExpr):
            self._process_expr(node.value, frame)
            self._bind_target(frame, node.target, _expr_references(node.value, frame), node)
            return
        for child in ast.iter_child_nodes(node):
            self._process_expr(child, frame)
        if isinstance(node, ast.Call):
            self._emit_call(node, frame)

    @staticmethod
    def _binding_signature(binding: Binding | None) -> tuple | None:
        if binding is None:
            return None
        return tuple((value.target, value.dynamic_path_pattern, value.pattern_kind) for value in binding.values)

    def _branch(self, frame: ScopeFrame, node: ast.AST, branches: list[list[ast.stmt]]) -> None:
        baseline = dict(frame.bindings)
        outcomes: list[dict[str, Binding]] = []
        for statements in branches:
            branch_frame = ScopeFrame(frame.scope_id, frame.scope_type, frame.qualified_name, frame.parent, dict(baseline))
            self._process_body(statements, branch_frame)
            outcomes.append(branch_frame.bindings)
        names = set(baseline)
        for outcome in outcomes:
            names.update(outcome)
        merged = dict(baseline)
        for name in names:
            candidates = [outcome.get(name) for outcome in outcomes]
            signatures = {self._binding_signature(candidate) for candidate in candidates}
            if len(signatures) == 1:
                candidate = candidates[0]
                if candidate is not None:
                    merged[name] = candidate
                else:
                    merged.pop(name, None)
                continue
            values: dict[tuple, Reference] = {}
            for candidate in candidates:
                if candidate:
                    for value in candidate.values:
                        values[(value.target, value.dynamic_path_pattern, value.pattern_kind)] = value
            temp = ScopeFrame(frame.scope_id, frame.scope_type, frame.qualified_name, frame.parent, merged)
            self._bind(temp, name, list(values.values()), node, "LOW")
            merged[name] = temp.bindings[name]
        frame.bindings = merged

    def _process_stmt(self, node: ast.stmt, frame: ScopeFrame) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                self._process_expr(decorator, frame)
            for default in [*node.args.defaults, *node.args.kw_defaults]:
                self._process_expr(default, frame)
            child = self._scope(node, "ASYNC_FUNCTION" if isinstance(node, ast.AsyncFunctionDef) else "FUNCTION", node.name, frame)
            for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
                self._bind(child, arg.arg, [], arg)
            if node.args.vararg:
                self._bind(child, node.args.vararg.arg, [], node.args.vararg)
            if node.args.kwarg:
                self._bind(child, node.args.kwarg.arg, [], node.args.kwarg)
            self._process_body(node.body, child)
            return
        if isinstance(node, ast.ClassDef):
            child = self._scope(node, "CLASS", node.name, frame)
            self._process_body(node.body, child)
            return
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            self._process_expr(value, frame)
            refs = _expr_references(value, frame)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                self._bind_target(frame, target, refs, node)
            return
        if isinstance(node, ast.AugAssign):
            self._process_expr(node.value, frame)
            values = _combine_values(_expr_references(node.target, frame), _expr_references(node.value, frame), "" if isinstance(node.op, ast.Add) else "/")
            self._bind_target(frame, node.target, values, node)
            return
        if isinstance(node, ast.If):
            self._process_expr(node.test, frame)
            branches = [node.body, node.orelse or []]
            self._branch(frame, node, branches)
            return
        if isinstance(node, (ast.For, ast.AsyncFor)):
            self._process_expr(node.iter, frame)
            baseline: list[ast.stmt] = []
            body = [ast.Assign(targets=[node.target], value=ast.Constant(value=None), lineno=node.lineno), *node.body]
            self._branch(frame, node, [baseline, body])
            self._process_body(node.orelse, frame)
            return
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                self._process_expr(item.context_expr, frame)
                if item.optional_vars is not None:
                    refs = []
                    if isinstance(item.context_expr, ast.Call) and _call_name(item.context_expr) == "open" and item.context_expr.args:
                        refs = _expr_references(item.context_expr.args[0], frame)
                    self._bind_target(frame, item.optional_vars, refs, node)
            self._process_body(node.body, frame)
            return
        if isinstance(node, ast.Try):
            branches = [node.body, *[handler.body for handler in node.handlers]]
            if node.orelse:
                branches.append(node.orelse)
            self._branch(frame, node, branches)
            self._process_body(node.finalbody, frame)
            return
        if isinstance(node, ast.Expr):
            self._process_expr(node.value, frame)
            return
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                self._process_stmt(child, frame)
            else:
                self._process_expr(child, frame)

    def _process_body(self, body: list[ast.stmt], frame: ScopeFrame) -> None:
        for statement in body:
            self._process_stmt(statement, frame)

    def run(self) -> list[dict]:
        module = self._scope(self.tree, "MODULE", "<module>", None)
        self._process_body(self.tree.body, module)
        for line_number, line in enumerate(self.lines, start=1):
            for target, resolution in extract_report_references(line):
                if (line_number, target) in self.used:
                    continue
                stripped = line.strip()
                if self.source_file.startswith("tests/"):
                    reference_type, direction, confidence = "TEST_REFERENCE", "TEST", "HIGH"
                elif re.search(r"href\s*=|_href\b|report_href", line, re.IGNORECASE):
                    reference_type, direction, confidence = "STATIC_LINK", "LINK", "HIGH"
                elif re.search(r"\b(?:print|logger\.|logging\.)", line) or stripped.startswith("#"):
                    reference_type, direction, confidence = "EXAMPLE_REFERENCE", "NONE", "LOW"
                elif resolution == "DYNAMIC":
                    reference_type, direction, confidence = "DYNAMIC_PATH_PATTERN", "UNKNOWN", "LOW"
                else:
                    reference_type, direction, confidence = "PATH_DECLARATION", "DECLARATION", "MEDIUM"
                self.rows.append(
                    _record(
                        source_file=self.source_file,
                        line_start=line_number,
                        line_end=line_number,
                        target=target,
                        resolution=resolution,
                        reference_type=reference_type,
                        direction=direction,
                        parser_type="PYTHON_AST",
                        confidence=confidence,
                        excerpt=line,
                        source_tree_commit=self.source_tree_commit,
                    )
                )
        return self.rows


def _python_rows(source_file: str, text: str, source_tree_commit: str) -> list[dict]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _line_rows(source_file, text, source_tree_commit, parser_type="PYTHON_FALLBACK")
    return _PythonAnalyzer(source_file, text, source_tree_commit, tree).run()


def _line_rows(source_file: str, text: str, source_tree_commit: str, parser_type: str) -> list[dict]:
    rows: list[dict] = []
    fenced = False
    suffix = Path(source_file).suffix.lower()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if parser_type == "SHELL":
            copy_move_rows = _shell_copy_move_rows(
                source_file, line, line_number, source_tree_commit
            )
            if copy_move_rows is not None:
                rows.extend(copy_move_rows)
                continue
        if suffix in {".md", ".txt"} and line.strip().startswith("```"):
            fenced = not fenced
        refs = extract_report_references(line)
        for target, resolution in refs:
            lower = line.lower()
            dynamic = resolution == "DYNAMIC"
            if source_file.startswith("tests/"):
                reference_type, direction, confidence = "TEST_REFERENCE", "TEST", "HIGH"
            elif suffix in {".md", ".txt"}:
                if fenced:
                    reference_type, direction, confidence = "EXAMPLE_REFERENCE", "NONE", "LOW"
                elif source_file.startswith("reports/"):
                    reference_type, direction, confidence = "HISTORICAL_REFERENCE", "NONE", "MEDIUM"
                elif source_file in {"PROJECT_INDEX.md", "docs/current_project_state.md", "docs/current_phase_status.json"}:
                    reference_type, direction, confidence = "STATE_INDEX_REFERENCE", "NONE", "HIGH"
                else:
                    reference_type, direction, confidence = "DOCUMENTATION_LINK", "NONE", "MEDIUM"
            elif suffix in {".html", ".css"}:
                reference_type, direction, confidence = (
                    ("STATIC_LINK", "LINK", "HIGH")
                    if "href" in lower or "url(" in lower
                    else ("DOCUMENTATION_LINK", "NONE", "LOW")
                )
            elif suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
                if re.search(r"\b(?:fetch|axios\.(?:get|post)|\.get)\s*\(", line):
                    reference_type = "DASHBOARD_RUNTIME_READ" if source_file.startswith("dashboard/") else "APP_RUNTIME_READ"
                    direction, confidence = "CONSUMER", "HIGH"
                elif "href" in lower:
                    reference_type, direction, confidence = "STATIC_LINK", "LINK", "HIGH"
                elif dynamic:
                    reference_type, direction, confidence = "DYNAMIC_PATH_PATTERN", "UNKNOWN", "LOW"
                else:
                    reference_type, direction, confidence = "PATH_DECLARATION", "DECLARATION", "MEDIUM"
            elif suffix in {".sh", ".command"} or source_file == "Makefile":
                target_token = re.escape(target)
                if re.search(rf"(?:>>?|\btee(?:\s+-a)?)\s+[\"']?{target_token}", line):
                    reference_type, direction, confidence = "PRODUCER_WRITE", "PRODUCER", "HIGH"
                elif re.search(rf"--(?:output|status-json|report|destination)[=\s]+[\"']?{target_token}", line):
                    reference_type, direction, confidence = "PRODUCER_WRITE", "PRODUCER", "HIGH"
                elif re.search(r"\b(?:cat|jq|grep|awk|test\s+-[fers]|\[\s+-[fers])\b", line):
                    reference_type, direction, confidence = "CONSUMER_READ", "CONSUMER", "HIGH"
                elif dynamic:
                    reference_type, direction, confidence = "DYNAMIC_PATH_PATTERN", "UNKNOWN", "LOW"
                else:
                    reference_type, direction, confidence = "PATH_DECLARATION", "DECLARATION", "MEDIUM"
            elif source_file.startswith("reports/"):
                reference_type, direction, confidence = "HISTORICAL_REFERENCE", "NONE", "MEDIUM"
            elif source_file in {"PROJECT_INDEX.md", "docs/current_project_state.md", "docs/current_phase_status.json"}:
                reference_type, direction, confidence = "STATE_INDEX_REFERENCE", "NONE", "HIGH"
            elif dynamic:
                reference_type, direction, confidence = "DYNAMIC_PATH_PATTERN", "UNKNOWN", "LOW"
            else:
                reference_type, direction, confidence = "PATH_DECLARATION", "DECLARATION", "MEDIUM"
            if dynamic and confidence == "HIGH":
                confidence = "MEDIUM"
            rows.append(
                _record(
                    source_file=source_file,
                    line_start=line_number,
                    line_end=line_number,
                    target=target,
                    resolution=resolution,
                    reference_type=reference_type,
                    direction=direction,
                    parser_type=parser_type,
                    confidence=confidence,
                    excerpt=line,
                    source_tree_commit=source_tree_commit,
                )
            )
    return rows


def classify_source_text(source_file: str, text: str, source_tree_commit: str = "TEST") -> list[dict]:
    suffix = Path(source_file).suffix.lower()
    if suffix == ".py":
        rows = _python_rows(source_file, text, source_tree_commit)
    else:
        parser = (
            "SHELL"
            if suffix in {".sh", ".command"} or source_file == "Makefile"
            else "MARKDOWN"
            if suffix in {".md", ".txt"}
            else "FRONTEND"
            if suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".html", ".css"}
            else "STRUCTURED_TEXT"
        )
        rows = _line_rows(source_file, text, source_tree_commit, parser)
    unique = {row["reference_id"]: row for row in rows}
    return sorted(
        unique.values(),
        key=lambda row: (
            row["normalized_target"],
            row["source_file"],
            row["source_line_start"],
            row["reference_type"],
            row["reference_id"],
        ),
    )
