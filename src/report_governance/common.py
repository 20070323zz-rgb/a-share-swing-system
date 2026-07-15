from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class RunContext:
    root: Path
    config: dict[str, Any]
    source_tree_commit: str
    generated_at: str
    run_id: str
    snapshot_revision: str
    supersedes: str


def load_config(root: Path, path: str = "configs/report_governance_phase_ar.json") -> dict[str, Any]:
    return json.loads((root / path).read_text(encoding="utf-8"))


def git_output(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def create_run_context(
    root: Path,
    config: dict[str, Any],
    source_tree_commit: str | None = None,
) -> RunContext:
    commit = source_tree_commit or git_output(root, "rev-parse", "HEAD")
    resolved_commit = git_output(root, "rev-parse", f"{commit}^{{commit}}")
    if resolved_commit != commit:
        commit = resolved_commit
    commit_time = git_output(root, "show", "-s", "--format=%cI", commit)
    generated_at = datetime.fromisoformat(commit_time).astimezone(ZoneInfo("Asia/Shanghai")).isoformat()
    config_hash = sha256_bytes(canonical_json(config))
    run_id = stable_id("phase-ar-run", commit, config_hash, length=24)
    return RunContext(
        root=root,
        config=config,
        source_tree_commit=commit,
        generated_at=generated_at,
        run_id=run_id,
        snapshot_revision=config["snapshot_revision"],
        supersedes=config["supersedes"],
    )


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(namespace: str, *parts: object, length: int = 20) -> str:
    payload = "\x1f".join([namespace, *(str(part) for part in parts)]).encode("utf-8")
    return f"{namespace}_{hashlib.sha256(payload).hexdigest()[:length]}"


def posix_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalized_relative(value: str) -> str:
    cleaned = value.replace("\\", "/").strip().lstrip("./")
    while "//" in cleaned:
        cleaned = cleaned.replace("//", "/")
    return PurePosixPath(cleaned).as_posix()


def path_is_within(relative_path: str, roots: Iterable[str]) -> bool:
    path = PurePosixPath(normalized_relative(relative_path))
    for root in roots:
        candidate = PurePosixPath(normalized_relative(root))
        if path == candidate or candidate in path.parents:
            return True
    return False


def read_text_lossy(path: Path, limit: int | None = None) -> str:
    data = path.read_bytes()
    if limit is not None:
        data = data[:limit]
    return data.decode("utf-8", errors="replace")


def source_files(context: RunContext) -> list[Path]:
    allowed = set(context.config["source_extensions"])
    excluded = [normalized_relative(item) for item in context.config["excluded_source_roots"]]
    files: list[Path] = []
    for root_name in context.config["active_source_roots"]:
        root = context.root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed:
                continue
            relative = posix_relative(path, context.root)
            if path_is_within(relative, excluded):
                continue
            if "artifact_type" in read_text_lossy(path, limit=4096) and "GOVERNANCE_CONTROL" in read_text_lossy(path, limit=4096):
                continue
            files.append(path)
    for relative in context.config.get("authority_source_files", []):
        path = context.root / relative
        if path.is_file():
            files.append(path)
    return sorted(set(files), key=lambda item: posix_relative(item, context.root))


def metadata(context: RunContext, artifact_type: str, version: str, record_count: int) -> dict[str, Any]:
    return {
        "artifact_type": artifact_type,
        "schema_version": version,
        "snapshot_revision": context.snapshot_revision,
        "supersedes": context.supersedes,
        "source_tree_commit": context.source_tree_commit,
        "generated_at": context.generated_at,
        "immutable": True,
        "structured_scanner_version": context.config["structured_scanner_version"],
        "backstop_scanner_version": context.config["backstop_scanner_version"],
        "evidence_schema_version": context.config["evidence_schema_version"],
        "review_schema_version": context.config["review_schema_version"],
        "run_id": context.run_id,
        "record_count": record_count,
    }
