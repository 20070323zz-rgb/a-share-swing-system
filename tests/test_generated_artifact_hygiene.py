import csv
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.archive_low_risk_reports import write_csv as write_archive_csv
from scripts.project_hygiene_audit import write_csv as write_hygiene_csv
from src.chatgpt_weekly_packet import normalize_markdown


def test_governance_csv_writers_use_lf(tmp_path: Path) -> None:
    fields = ["path", "reason"]
    rows = [{"path": "reports/example.md", "reason": "可再生"}]

    for index, writer in enumerate((write_hygiene_csv, write_archive_csv)):
        target = tmp_path / f"artifact_{index}.csv"
        writer(target, rows, fields)
        raw = target.read_bytes()

        assert b"\r\n" not in raw
        assert raw.count(b"\n") == 2
        with target.open(newline="", encoding="utf-8") as file:
            assert list(csv.DictReader(file)) == rows


def test_markdown_normalizer_removes_line_end_whitespace() -> None:
    normalized = normalize_markdown("title  \nbody\t\n\n")

    assert normalized == "title\nbody\n"
    assert all(not line.endswith((" ", "\t")) for line in normalized.splitlines())
