from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from .common import pretty_json, sha256_bytes


def immutable_write(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_bytes()
        if existing != content:
            raise FileExistsError(f"immutable snapshot differs: {path}")
        return "IDEMPOTENT"
    path.write_bytes(content)
    return "CREATED"


def json_bytes(metadata: dict[str, Any], records: list[dict[str, Any]]) -> bytes:
    return pretty_json({"metadata": metadata, "records": records})


def csv_bytes(records: list[dict[str, Any]]) -> bytes:
    if not records:
        return b"\n"
    fieldnames = list(records[0])
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({key: _cell(record.get(key)) for key in fieldnames})
    return output.getvalue().encode("utf-8")


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if value is None:
        return ""
    return value


def markdown_table(title: str, records: list[dict[str, Any]], fields: list[str], metadata: dict[str, Any]) -> bytes:
    lines = [f"# {title}", "", *(f"- {key}: `{value}`" for key, value in metadata.items()), ""]
    lines.extend(["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"])
    for record in records:
        values = [str(_cell(record.get(field, ""))).replace("|", "\\|").replace("\n", " ") for field in fields]
        lines.append("| " + " | ".join(values) + " |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def content_record(path: Path, root: Path) -> dict[str, str]:
    content = path.read_bytes()
    return {"relative_path": path.relative_to(root).as_posix(), "content_sha256": sha256_bytes(content)}
