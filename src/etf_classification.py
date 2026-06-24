"""Backward-compatible wrapper for ETF classification.

The canonical phase2 entrypoint is ``src/etf_classifier.py``. This module is
kept so existing research scripts that import ``etf_classification`` continue
to work.
"""

from __future__ import annotations

from etf_classifier import (  # noqa: F401
    CLASSIFICATION_FILE,
    LEGACY_CLASSIFICATION_FILE,
    REPORT_FILE,
    build_classification,
    classify_etf,
    main,
)


if __name__ == "__main__":
    main()
