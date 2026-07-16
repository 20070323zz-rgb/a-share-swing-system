from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from src.report_governance.authority_merge import AuthorityMergeError, apply_owned_overlay
from src.report_governance.backstop_scanner import QUERY_TYPES, scan_backstop_references
from src.report_governance.common import RunContext, canonical_json, create_run_context, load_config, metadata, source_files
from src.report_governance.disagreement import DISAGREEMENT_TYPES, build_scanner_disagreements
from src.report_governance.evidence import (
    add_disagreement_evidence,
    add_manual_review_evidence,
    build_evidence_index,
    evidence_lookup_maps,
)
from src.report_governance.inventory import (
    build_inventory,
    infer_business_date,
    validate_inventory_content_hashes,
)
from src.report_governance.pipeline import build_phase_ar
from src.report_governance.readiness import build_migration_readiness
from src.report_governance.reference_index import build_reference_index
from src.report_governance.snapshot import immutable_write
from src.report_governance.structured_scanner import ExpressionResolver, scan_structured_references
from src.report_governance.temporal import valid_date_token, valid_month_token


ROOT = Path(__file__).resolve().parents[1]


def _state(context: RunContext) -> dict[str, object]:
    inventory = build_inventory(context)
    structured = scan_structured_references(context, inventory)
    backstop = scan_backstop_references(context, inventory)
    evidence = build_evidence_index(context, inventory, structured, backstop)
    structured_ids, backstop_ids = evidence_lookup_maps(evidence)
    disagreements = build_scanner_disagreements(
        context, inventory, structured, backstop, structured_ids, backstop_ids
    )
    evidence = add_disagreement_evidence(context, evidence, disagreements)
    active = build_reference_index(context, inventory, structured, backstop, disagreements)
    readiness, reviews = build_migration_readiness(
        context, inventory, active, evidence, structured, backstop
    )
    evidence = add_manual_review_evidence(context, evidence, readiness, reviews)
    return {
        "context": context,
        "inventory": inventory,
        "structured": structured,
        "backstop": backstop,
        "disagreements": disagreements,
        "active": active,
        "evidence": evidence,
        "readiness": readiness,
        "reviews": reviews,
    }


@pytest.fixture(scope="session")
def governance_state():
    return _state(create_run_context(ROOT, load_config(ROOT)))


def _temp_context(tmp_path: Path, *, authority_files: list[str] | None = None) -> RunContext:
    config = dict(load_config(ROOT))
    config.update(
        {
            "report_roots": ["reports"],
            "active_source_roots": ["src", "scripts", "configs"],
            "authority_source_files": authority_files or [],
            "excluded_source_roots": ["reports", "tests"],
            "governance_control_roots": ["reports/governance/phase_ar"],
            "archive_roots": ["reports/archive"],
            "formal_execution_inputs": [],
            "app_dashboard_entrypoints": [],
            "availability_active_prefixes": [],
        }
    )
    return RunContext(
        root=tmp_path,
        config=config,
        source_tree_commit="a" * 40,
        generated_at="2026-07-16T08:00:00+08:00",
        run_id="phase-ar-test-run",
        snapshot_revision=config["snapshot_revision"],
        supersedes=config["supersedes"],
    )


def _write_reports(tmp_path: Path, names: list[str]) -> None:
    for name in names:
        path = tmp_path / "reports" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"report: {name}\n", encoding="utf-8")


def test_inventory_is_deterministic_complete_and_hash_valid(governance_state):
    context = governance_state["context"]
    inventory = governance_state["inventory"]
    assert inventory == build_inventory(context)
    assert len(inventory) == 651
    assert len({item["report_id"] for item in inventory}) == len(inventory)
    assert not any(item["relative_path"].startswith("reports/governance/phase_ar/") for item in inventory)
    validate_inventory_content_hashes(context, inventory)


def test_inventory_hash_change_requires_rebuild(tmp_path):
    _write_reports(tmp_path, ["same_path.json"])
    context = _temp_context(tmp_path)
    before = build_inventory(context)
    (tmp_path / "reports/same_path.json").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory content hash mismatch"):
        validate_inventory_content_hashes(context, before)
    after = build_inventory(context)
    assert before[0]["relative_path"] == after[0]["relative_path"]
    assert before[0]["content_sha256"] != after[0]["content_sha256"]
    validate_inventory_content_hashes(context, after)


def test_snapshot_source_commit_is_actual_generation_commit(governance_state):
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    context = governance_state["context"]
    assert context.source_tree_commit == actual
    payload = metadata(context, "TEST", "v2", 1)
    assert payload["source_tree_commit"] == actual
    assert payload["snapshot_revision"] == "phase-ar-v2-2026-07-16"
    assert payload["supersedes"] == "phase-ar-v1-2026-07-15"
    assert payload["generated_at"].endswith("+08:00")


def test_business_date_never_uses_mtime(tmp_path):
    path = tmp_path / "report_without_date.md"
    path.write_text("# no business date\n", encoding="utf-8")
    assert infer_business_date(path) == (None, False)
    path.write_text("generated_at: 2026-07-15 12:00:00\n", encoding="utf-8")
    assert infer_business_date(path) == ("2026-07-15", True)


def test_stable_artifact_naming_is_not_forced_to_date(tmp_path):
    _write_reports(tmp_path, ["phase_contract.md", "allocation_decision.md", "event_snapshot.md"])
    (tmp_path / "reports/event_snapshot.md").write_text("business_date: 2026-07-16\n", encoding="utf-8")
    records = {item["filename"]: item for item in build_inventory(_temp_context(tmp_path))}
    assert records["phase_contract.md"]["naming_status"] == "STABLE_DECISION_ARTIFACT"
    assert records["allocation_decision.md"]["naming_status"] == "STABLE_DECISION_ARTIFACT"
    assert records["event_snapshot.md"]["naming_status"] == "NEEDS_DATE_NORMALIZATION"


def test_date_and_month_tokens_are_strict():
    assert valid_date_token("2026-07-15")
    assert valid_date_token("20260715")
    assert not valid_date_token("2026-02-29")
    assert not valid_date_token("2026-99-99")
    assert not valid_date_token("2026-07")
    assert valid_month_token("2026-07")
    assert not valid_month_token("202607")
    assert valid_month_token("202607", allow_compact=True)


def test_markdown_links_images_examples_and_code_blocks_are_documentation(tmp_path):
    names = [f"doc_{index}.md" for index in range(12)]
    _write_reports(tmp_path, names)
    docs = tmp_path / "docs/authority.md"
    docs.parent.mkdir(parents=True)
    lines = [f"[doc](reports/{name})" for name in names[:4]]
    lines += [f"![image](reports/{name})" for name in names[4:7]]
    lines += [f"example `reports/{name}`" for name in names[7:10]]
    lines += ["```text", *[f"reports/{name}" for name in names[10:]], "```"]
    docs.write_text("\n".join(lines) + "\n", encoding="utf-8")
    runtime = tmp_path / "src/runtime.py"
    runtime.parent.mkdir(parents=True)
    runtime.write_text('Path("reports/doc_0.md").read_text()\n', encoding="utf-8")
    context = _temp_context(tmp_path, authority_files=["docs/authority.md"])
    records = scan_structured_references(context, build_inventory(context))
    markdown = [item for item in records if item["source_path"] == "docs/authority.md"]
    assert len({item["report_path"] for item in markdown}) == 12
    assert {item["reference_class"] for item in markdown} <= {
        "DOCUMENTATION_REFERENCE",
        "DOCUMENTATION_EXAMPLE",
        "CODE_BLOCK_REFERENCE",
    }
    assert all(item["direction"] == "REFERENCE" for item in markdown)
    assert any(item["report_path"] == "reports/doc_0.md" and item["direction"] == "CONSUMER" for item in records)


def test_python_and_shell_file_operations_preserve_direction(tmp_path):
    operation_names = [
        "src.json", "copy.json", "copy2.json", "copyfile.json", "move.json",
        "os_replace.json", "os_rename.json", "path_replace.json", "path_rename.json",
        "cp.json", "mv.json", "dynamic_2026-07-16.json",
    ]
    _write_reports(tmp_path, operation_names)
    source = tmp_path / "src/operations.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        """import os\nimport shutil\nfrom pathlib import Path\nsrc = Path('reports/src.json')\nshutil.copy(src, Path('reports/copy.json'))\nshutil.copy2(src, Path('reports/copy2.json'))\nshutil.copyfile(src, Path('reports/copyfile.json'))\nshutil.move(src, Path('reports/move.json'))\nos.replace(src, Path('reports/os_replace.json'))\nos.rename(src, Path('reports/os_rename.json'))\nsrc.replace(Path('reports/path_replace.json'))\nsrc.rename(Path('reports/path_rename.json'))\ndynamic = Path(f'reports/dynamic_{2026}-07-16.json')\ndynamic.write_text('x')\n""",
        encoding="utf-8",
    )
    shell = tmp_path / "scripts/operations.sh"
    shell.parent.mkdir(parents=True)
    shell.write_text("cp reports/src.json reports/cp.json\nmv reports/src.json reports/mv.json\n", encoding="utf-8")
    context = _temp_context(tmp_path)
    records = scan_structured_references(context, build_inventory(context))
    short_operations = {item["operation"].rsplit(".", 1)[-1] for item in records if item["operation"]}
    assert {"copy", "copy2", "copyfile", "move", "replace", "rename", "cp", "mv"} <= short_operations
    for destination in operation_names[1:11]:
        assert any(item["report_path"] == f"reports/{destination}" and item["direction"] == "PRODUCER" for item in records)
    assert any(item["report_path"] == "reports/src.json" and item["direction"] == "MOVE_SOURCE" for item in records)
    assert any(item["dynamic_pattern"] and item["confidence"] == "MEDIUM" for item in records)


def test_backstop_has_all_independent_query_capabilities_and_boundaries(tmp_path):
    _write_reports(tmp_path, ["target.json", "daily_signal_2026-07-16.md"])
    src = tmp_path / "src/references.py"
    src.parent.mkdir(parents=True)
    src.write_text(
        """from pathlib import Path\nexact = 'reports/target.json'\njoined = 'reports/' + 'target.json'\nconstructed = Path('reports') / 'target.json'\ndynamic = Path(f'reports/daily_signal_{date}.md')\n""",
        encoding="utf-8",
    )
    config = tmp_path / "configs/runtime.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("report_path: reports/target.json\n", encoding="utf-8")
    shell = tmp_path / "scripts/run.sh"
    shell.parent.mkdir(parents=True)
    shell.write_text("cat reports/target.json\n", encoding="utf-8")
    context = _temp_context(tmp_path)
    records = scan_backstop_references(context, build_inventory(context))
    target = [item for item in records if item["report_path"] == "reports/target.json"]
    assert {item["query_type"] for item in target} == set(QUERY_TYPES)
    found = {item["query_type"] for item in target if item["result_status"] == "FOUND_REFERENCE"}
    assert {"EXACT_RELATIVE_PATH", "EXACT_BASENAME", "EXACT_STEM", "CONFIG_KEY_VALUE", "SHELL_TOKEN", "STRING_CONCAT", "PATH_CONSTRUCT"} <= found
    dynamic = [item for item in records if item["report_path"] == "reports/daily_signal_2026-07-16.md"]
    assert any(item["query_type"] == "DYNAMIC_PREFIX_EXTENSION" and item["result_status"] == "FOUND_REFERENCE" for item in dynamic)
    assert {item["result_status"] for item in records} <= {"FOUND_REFERENCE", "ZERO_RESULT_PROOF", "AMBIGUOUS_REFERENCE"}


def test_32_basename_substring_false_locks_are_rejected(tmp_path):
    names = [f"status_{index}.json" for index in range(32)]
    _write_reports(tmp_path, names)
    source = tmp_path / "src/similar.py"
    source.parent.mkdir(parents=True)
    source.write_text("\n".join(f"'data_update_status_{index}.json'" for index in range(32)) + "\n", encoding="utf-8")
    context = _temp_context(tmp_path)
    records = scan_backstop_references(context, build_inventory(context))
    exact_basename = [item for item in records if item["query_type"] == "EXACT_BASENAME"]
    assert len(exact_basename) == 32
    assert all(item["result_status"] == "ZERO_RESULT_PROOF" for item in exact_basename)


def test_known_43_active_reference_regressions_are_fail_closed(governance_state):
    fixture = json.loads((ROOT / "tests/fixtures/report_governance/known_active_reference_regressions.json").read_text())
    records = fixture["records"]
    assert len(records) == 43
    active = {item["relative_path"]: item for item in governance_state["active"]}
    readiness = {item["relative_path"]: item for item in governance_state["readiness"]}
    for case in records:
        path = case["report_path"]
        assert active[path]["structured_runtime_reference_count"] + active[path]["backstop_active_query_count"] > 0, path
        assert readiness[path]["migration_readiness"] == case["expected_status"], path
        assert not readiness[path]["migration_readiness"].startswith("PROVISIONALLY_SAFE"), path
        if case["producer_or_consumer"] == "PRODUCER":
            assert active[path]["structured_producer_count"] > 0, path


def test_app_dashboard_runtime_recall_is_complete(governance_state):
    active = {item["relative_path"]: item for item in governance_state["active"]}
    for path in governance_state["context"].config["app_dashboard_entrypoints"]:
        assert active[path]["structured_runtime_reference_count"] > 0, path


def test_archive_deletion_and_zero_move_boundaries(governance_state):
    readiness = governance_state["readiness"]
    archived = [item for item in readiness if "/archive/" in item["relative_path"]]
    assert len(archived) == 45 + 49
    assert all(item["migration_readiness"] == "NOT_APPLICABLE_ALREADY_ARCHIVED" for item in archived)
    assert not any(item["migration_readiness"].startswith("PROVISIONALLY_SAFE") for item in archived)
    assert not any(item["deletion_readiness"] == "SAFE_TO_DELETE_AFTER_AUTHORIZATION" for item in readiness)


def test_evidence_is_complete_resolvable_and_non_orphan(governance_state):
    evidence = governance_state["evidence"]
    evidence_ids = {item["evidence_id"] for item in evidence}
    assert len(evidence_ids) == len(evidence)
    required_types = {
        "STRUCTURED_PRODUCER", "STRUCTURED_CONSUMER", "BACKSTOP_REFERENCE", "BACKSTOP_ZERO_RESULT",
        "RUNTIME_LOCK", "SCANNER_DISAGREEMENT", "ALIAS", "ROLE", "RETENTION", "NAMING", "LOCATION",
    }
    if any(item["machine_provisional_before_review"] for item in governance_state["readiness"]):
        required_types.add("MANUAL_REVIEW")
    assert required_types <= {item["evidence_type"] for item in evidence}
    referenced: set[str] = set()
    for decision in governance_state["readiness"]:
        assert decision["decision_evidence_ids"]
        assert set(decision["decision_evidence_ids"]) <= evidence_ids
        referenced.update(decision["decision_evidence_ids"])
    assert referenced == evidence_ids
    assert all(item["source_tree_commit"] and item["scanner_version"] and item["evidence_hash"] for item in evidence)


def test_scanner_disagreement_is_structured_and_fail_closed(governance_state):
    disagreements = governance_state["disagreements"]
    assert disagreements
    required = {
        "disagreement_id", "report_id", "report_path", "disagreement_type", "structured_result",
        "backstop_result", "structured_evidence_ids", "backstop_evidence_ids", "severity",
        "resolution_status", "reviewer_verdict", "reviewer_evidence_ids", "source_tree_commit",
    }
    readiness = {item["report_id"]: item for item in governance_state["readiness"]}
    for item in disagreements:
        assert required <= set(item)
        assert item["disagreement_type"] in DISAGREEMENT_TYPES
        assert item["resolution_status"] == "UNRESOLVED"
        assert item["reviewer_evidence_ids"]
        assert not readiness[item["report_id"]]["migration_readiness"].startswith("PROVISIONALLY_SAFE")


def test_candidates_have_100_percent_individual_manual_review(governance_state):
    candidates = [item for item in governance_state["readiness"] if item["machine_provisional_before_review"]]
    reviews = governance_state["reviews"]
    assert len(candidates) == len(reviews)
    assert {item["report_id"] for item in candidates} == {item["report_id"] for item in reviews}
    query_fields = {
        "exact_path_query", "basename_query", "stem_query", "dynamic_prefix_query", "config_query",
        "shell_token_query", "string_concat_query", "path_construct_query",
    }
    for review in reviews:
        assert query_fields <= set(review)
        assert review["structured_evidence_ids"] is not review["backstop_evidence_ids"]
        assert review["zero_result_evidence_ids"]
        assert review["final_reviewer_verdict"] == "PASS"
        assert review["source_tree_commit"] == governance_state["context"].source_tree_commit
        assert review["reviewed_at"].endswith("+08:00")
        unhashed = {key: value for key, value in review.items() if key != "review_evidence_hash"}
        assert review["review_evidence_hash"] == hashlib.sha256(canonical_json(unhashed)).hexdigest()


def test_markdown_runtime_misclassification_is_zero(governance_state):
    markdown = [item for item in governance_state["structured"] if item["reference_kind"] == "MARKDOWN_REFERENCE"]
    assert len(markdown) >= 20
    assert all(item["reference_class"] in {"DOCUMENTATION_REFERENCE", "DOCUMENTATION_EXAMPLE", "CODE_BLOCK_REFERENCE"} for item in markdown)


def test_dynamic_report_templates_are_materialized(governance_state):
    daily = [item for item in governance_state["structured"] if "daily_signal_" in item["report_path"]]
    weekly = [item for item in governance_state["structured"] if "weekly_review_" in item["report_path"]]
    assert any(item["direction"] == "PRODUCER" for item in daily)
    assert any(item["direction"] == "PRODUCER" for item in weekly)


def test_class_method_path_lookup_requires_explicit_scope():
    resolver = ExpressionResolver(
        {
            "self.OUTPUT": "reports/class_output.md",
            "cls.OUTPUT": "reports/class_output.md",
            "Writer.OUTPUT": "reports/class_output.md",
        }
    )
    assert resolver.resolve(ast.parse("OUTPUT", mode="eval").body) is None
    assert resolver.resolve(ast.parse("self.OUTPUT", mode="eval").body) == "reports/class_output.md"
    assert resolver.resolve(ast.parse("cls.OUTPUT", mode="eval").body) == "reports/class_output.md"
    assert resolver.resolve(ast.parse("Writer.OUTPUT", mode="eval").body) == "reports/class_output.md"


def test_immutable_writer_is_idempotent_and_fail_fast(tmp_path):
    path = tmp_path / "snapshot.json"
    assert immutable_write(path, b"same\n") == "CREATED"
    assert immutable_write(path, b"same\n") == "IDEMPOTENT"
    with pytest.raises(FileExistsError):
        immutable_write(path, b"different\n")


def test_v1_snapshot_remains_immutable_and_self_verifying():
    root = ROOT / "reports/governance/phase_ar"
    manifest = json.loads((root / "immutable_governance_snapshot_manifest_v1_2026-07-15.json").read_text())
    rows: list[str] = []
    for item in manifest["files"]:
        actual = hashlib.sha256((root / item["relative_path"]).read_bytes()).hexdigest()
        assert actual == item["content_sha256"]
        rows.append(f"{item['relative_path']}\t{item['content_sha256']}\n")
    assert hashlib.sha256("".join(rows).encode()).hexdigest() == manifest["group_manifest_sha256"]


def test_phase_b_contract_has_all_fail_closed_clauses():
    text = (ROOT / "docs/reports_governance/phase_b_end_to_end_contract.md").read_text()
    for phrase in (
        "DATA_NOT_READY", "arbitrary older dated file", "runtime alias", "Freshness Gate", "Canonical SSOT",
        "launchd plist", "shell wrappers", "cron-compatible", "stdout and stderr", "immutable dated artifact",
        "business_date", "updated atomically", "must not guess", "previous alias remains intact",
    ):
        assert phrase in text


def test_authority_merge_preserves_availability_and_unknown_nested_fields():
    authority = {"availability": {"status": "ACTIVE", "unknown": {"keep": 1}}, "report_status": "OLD"}
    overlay = {"availability": {"status": "WRONG"}, "report_status": "ACTIVE"}
    with pytest.raises(AuthorityMergeError):
        apply_owned_overlay(authority, overlay, {"report_status"})
    merged = apply_owned_overlay(authority, {"report_status": "ACTIVE"}, {"report_status"})
    assert merged["availability"] == authority["availability"]
    assert merged["report_status"] == "ACTIVE"


def test_three_clean_rebuilds_are_byte_stable(tmp_path):
    roots = [tmp_path / f"run-{index}" for index in range(3)]
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    results = [build_phase_ar(ROOT, "2026-07-16", root, source_tree_commit=source_commit) for root in roots]
    hashes = [result["snapshot"]["group_manifest_sha256"] for result in results]
    assert len(set(hashes)) == 1
    relative_files = [item["relative_path"] for item in results[0]["snapshot"]["files"]]
    for relative in relative_files:
        assert len({(root / relative).read_bytes() for root in roots}) == 1
