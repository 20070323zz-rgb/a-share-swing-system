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


GENERATOR_VERSION = "2.1.0"
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
    if variable and "REPORT" in variable.group(1).upper():
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


def _expr_references(node: ast.AST | None, bindings: dict[str, list[Reference]]) -> list[Reference]:
    if node is None:
        return []
    if isinstance(node, ast.Name):
        return bindings.get(node.id, [])
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [Reference(*item) for item in extract_report_references(node.value)]
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append("{" + (ast.unparse(value.value) if hasattr(ast, "unparse") else "expr") + "}")
        return [Reference(*item) for item in extract_report_references("".join(parts))]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        text = ast.unparse(node) if hasattr(ast, "unparse") else ""
        return [Reference(*item) for item in extract_report_references(text)]
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        result: list[Reference] = []
        for item in node.elts:
            result.extend(_expr_references(item, bindings))
        return result
    if isinstance(node, ast.Dict):
        result: list[Reference] = []
        for item in [*node.keys, *node.values]:
            result.extend(_expr_references(item, bindings))
        return result
    if isinstance(node, ast.Call):
        text = ast.unparse(node) if hasattr(ast, "unparse") else ""
        direct = [Reference(*item) for item in extract_report_references(text)]
        if direct:
            return direct
        result: list[Reference] = []
        for item in node.args:
            result.extend(_expr_references(item, bindings))
        return result
    text = ast.unparse(node) if hasattr(ast, "unparse") else ""
    return [Reference(*item) for item in extract_report_references(text)]


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _call_receiver(call: ast.Call, bindings: dict[str, list[Reference]]) -> list[Reference]:
    return _expr_references(call.func.value, bindings) if isinstance(call.func, ast.Attribute) else []


def _runtime_read_type(source_file: str) -> str:
    if source_file.startswith(("app/backend/", "app/frontend/")):
        return "APP_RUNTIME_READ"
    if source_file.startswith("dashboard/"):
        return "DASHBOARD_RUNTIME_READ"
    return "CONSUMER_READ"


def _python_rows(source_file: str, text: str, source_tree_commit: str) -> list[dict]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _line_rows(source_file, text, source_tree_commit, parser_type="PYTHON_FALLBACK")
    lines = text.splitlines()
    binding_candidates: dict[str, list[list[Reference]]] = {}
    bindings: dict[str, list[Reference]] = {}
    used: set[tuple[int, str]] = set()
    rows: list[dict] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            refs = _expr_references(value, bindings)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target_node in targets:
                if isinstance(target_node, ast.Name) and refs:
                    binding_candidates.setdefault(target_node.id, []).append(refs)

    bindings = {}
    for name, candidates in binding_candidates.items():
        identities = {
            tuple((ref.target, ref.resolution) for ref in candidate)
            for candidate in candidates
        }
        if len(identities) == 1:
            bindings[name] = candidates[0]

    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        name = _call_name(call)
        operations: list[tuple[list[Reference], str]] = []
        if name == "open":
            refs = _expr_references(call.args[0], bindings) if call.args else []
            mode = "r"
            if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
                mode = str(call.args[1].value)
            for keyword in call.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = str(keyword.value.value)
            operations.append((refs, "PRODUCER" if any(flag in mode for flag in "wax+") else "CONSUMER"))
        elif name in PYTHON_PRODUCER_METHODS:
            refs = _call_receiver(call, bindings)
            if name in {"to_csv", "to_json", "to_parquet", "write_csv", "write_json"} and call.args:
                refs = _expr_references(call.args[0], bindings)
            elif name in {"dump", "safe_dump"} and len(call.args) > 1:
                refs = []
                for arg in call.args[1:]:
                    refs += _expr_references(arg, bindings)
            operations.append((refs, "PRODUCER"))
        elif name in PYTHON_CONSUMER_METHODS:
            refs = _call_receiver(call, bindings)
            for arg in call.args:
                refs += _expr_references(arg, bindings)
            operations.append((refs, "CONSUMER"))
        elif name in PYTHON_COPY_METHODS | PYTHON_ATOMIC_METHODS:
            args = list(call.args)
            receiver = _call_receiver(call, bindings)
            module_call = (
                isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id in {"os", "shutil"}
            )
            if module_call and len(args) >= 2:
                operations.append((_expr_references(args[0], bindings), "CONSUMER"))
                operations.append((_expr_references(args[1], bindings), "PRODUCER"))
            elif isinstance(call.func, ast.Attribute) and args:
                if receiver:
                    operations.append((receiver, "CONSUMER"))
                operations.append((_expr_references(args[0], bindings), "PRODUCER"))
            elif len(args) >= 2:
                operations.append((_expr_references(args[0], bindings), "CONSUMER"))
                operations.append((_expr_references(args[1], bindings), "PRODUCER"))
        elif name in {"fetch", "axios"}:
            refs: list[Reference] = []
            for arg in call.args:
                refs += _expr_references(arg, bindings)
            operations.append((refs, "CONSUMER"))

        end_lineno = getattr(call, "end_lineno", call.lineno)
        excerpt = "\n".join(lines[call.lineno - 1 : end_lineno])
        for refs, direction in operations:
            for ref in refs:
                reference_type = (
                    "TEST_REFERENCE"
                    if source_file.startswith("tests/")
                    else "DYNAMIC_PATH_PATTERN"
                    if ref.resolution == "DYNAMIC"
                    else "PRODUCER_WRITE"
                    if direction == "PRODUCER"
                    else _runtime_read_type(source_file)
                )
                confidence = "LOW" if ref.resolution == "DYNAMIC" else "HIGH"
                rows.append(
                    _record(
                        source_file=source_file,
                        line_start=call.lineno,
                        line_end=end_lineno,
                        target=ref.target,
                        resolution=ref.resolution,
                        reference_type=reference_type,
                        direction=direction,
                        parser_type="PYTHON_AST",
                        confidence=confidence,
                        excerpt=excerpt,
                        source_tree_commit=source_tree_commit,
                    )
                )
                used.add((call.lineno, ref.target))

    # Preserve declarations, links, logs and examples without promoting them to IO.
    for line_number, line in enumerate(lines, start=1):
        for target, resolution in extract_report_references(line):
            if (line_number, target) in used:
                continue
            stripped = line.strip()
            if source_file.startswith("tests/"):
                reference_type, direction, confidence = "TEST_REFERENCE", "TEST", "HIGH"
            elif re.search(r"href\s*=|_href\b|report_href", line, re.IGNORECASE):
                reference_type, direction, confidence = "STATIC_LINK", "LINK", "HIGH"
            elif re.search(r"\b(?:print|logger\.|logging\.)", line):
                reference_type, direction, confidence = "EXAMPLE_REFERENCE", "NONE", "LOW"
            elif stripped.startswith("#"):
                reference_type, direction, confidence = "EXAMPLE_REFERENCE", "NONE", "LOW"
            elif resolution == "DYNAMIC":
                reference_type, direction, confidence = "DYNAMIC_PATH_PATTERN", "UNKNOWN", "LOW"
            else:
                reference_type, direction, confidence = "PATH_DECLARATION", "DECLARATION", "MEDIUM"
            if resolution == "DYNAMIC" and confidence == "HIGH":
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
                    parser_type="PYTHON_AST",
                    confidence=confidence,
                    excerpt=line,
                    source_tree_commit=source_tree_commit,
                )
            )
    return rows


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
