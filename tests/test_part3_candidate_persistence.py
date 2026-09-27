import json
from pathlib import Path

import pytest

from src.part3_blocking import BlockingRun, CandidateSet
from src.part3_candidate_persistence import (
    load_persisted_candidates,
    persist_candidate_run,
    validate_persisted_candidates,
)


def _run() -> BlockingRun:
    return BlockingRun(
        strategy="test",
        target_source="S2",
        candidates=CandidateSet(
            {"S1-2": {"S2-3", "S2-1"}, "S1-1": set()}
        ),
        elapsed_seconds=0.0,
    )


def test_persist_and_validate_preserves_order_counts_and_zero_s1(tmp_path: Path) -> None:
    summary = persist_candidate_run(
        _run(), {"S1-1", "S1-2"}, tmp_path, "stage", 5
    )
    validated = validate_persisted_candidates(
        tmp_path, "stage", "S2", {"S1-1", "S1-2"}
    )
    assert validated == summary
    assert summary.candidate_rows == 2
    assert summary.zero_candidate_s1_count == 1
    assert load_persisted_candidates(tmp_path, "stage", "S2") == {
        "S1-2": {"S2-1", "S2-3"}
    }


def test_persisted_manifest_has_schema_and_threshold(tmp_path: Path) -> None:
    persist_candidate_run(
        _run(), {"S1-1", "S1-2"}, tmp_path, "stage", 25
    )
    manifest = json.loads(
        (tmp_path / "stage" / "S2" / "manifest.json").read_text()
    )
    assert manifest["schema_version"] == "m5.6.2-candidate-v1"
    assert manifest["threshold"] == 25


def test_validate_rejects_wrong_s1_universe(tmp_path: Path) -> None:
    persist_candidate_run(
        _run(), {"S1-1", "S1-2"}, tmp_path, "stage", 5
    )
    with pytest.raises(ValueError, match="S1 manifest"):
        validate_persisted_candidates(
            tmp_path, "stage", "S2", {"S1-1", "S1-3"}
        )
