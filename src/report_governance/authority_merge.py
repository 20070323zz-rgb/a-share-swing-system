from __future__ import annotations

from copy import deepcopy
from typing import Any


class AuthorityMergeError(ValueError):
    pass


def _owned(path: str, owned_paths: set[str]) -> bool:
    return any(path == item or path.startswith(f"{item}.") for item in owned_paths)


def apply_owned_overlay(authority: dict[str, Any], overlay: dict[str, Any], owned_paths: set[str]) -> dict[str, Any]:
    """Preserve authority data and apply only explicitly Reports-owned leaves."""
    result = deepcopy(authority)

    def visit(target: dict[str, Any], incoming: dict[str, Any], prefix: str = "") -> None:
        for key, value in incoming.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict) and not _owned(path, owned_paths):
                existing = target.get(key)
                if existing is None:
                    existing = {}
                    target[key] = existing
                if not isinstance(existing, dict):
                    raise AuthorityMergeError(f"unowned type conflict at {path}")
                visit(existing, value, path)
                continue
            if not _owned(path, owned_paths):
                if key in target and target[key] != value:
                    raise AuthorityMergeError(f"attempted unowned overwrite at {path}")
                continue
            target[key] = deepcopy(value)

    visit(result, overlay)
    return result
