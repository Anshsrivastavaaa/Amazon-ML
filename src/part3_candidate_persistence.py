"""Streaming persistence and replay validation for candidate identities."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

from src.part3_blocking import BlockingRun


@dataclass(frozen=True)
class CandidatePersistenceSummary:
    """Counts and checksums recorded for one persisted candidate stage."""

    stage_id: str
    target_source: str
    candidate_rows: int
    unique_candidate_keys: int
    validation_s1_count: int
    zero_candidate_s1_count: int
    candidate_checksum: str
    s1_manifest_checksum: str

    def as_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def _digest_line(digest: "hashlib._Hash", value: str) -> None:
    digest.update(value.encode("utf-8"))
    digest.update(b"\n")


def _stage_dir(root: Path, stage_id: str, target_source: str) -> Path:
    return root / stage_id / target_source


def persist_candidate_run(
    run: BlockingRun,
    validation_s1_ids: Iterable[str],
    root: Path,
    stage_id: str,
    threshold: int,
    split_fraction: float = 0.2,
    seed: int = 42,
) -> CandidatePersistenceSummary:
    """Persist one run with deterministic candidate and S1 manifest rows."""
    validation_ids = sorted(set(validation_s1_ids))
    if run.target_source not in {"S2", "S3"}:
        raise ValueError(f"Unsupported target source: {run.target_source}")
    output_dir = _stage_dir(root, stage_id, run.target_source)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_dir / "candidates.jsonl"
    s1_path = output_dir / "s1_manifest.jsonl"
    candidate_digest = hashlib.sha256()
    s1_digest = hashlib.sha256()
    candidate_rows = 0
    zero_count = 0

    with candidate_path.open("w", encoding="utf-8", newline="\n") as candidates:
        with s1_path.open("w", encoding="utf-8", newline="\n") as manifest:
            for source1_id in validation_ids:
                candidate_ids = sorted(
                    run.candidates.source1_to_candidates.get(source1_id, set())
                )
                if not candidate_ids:
                    zero_count += 1
                s1_record = {
                    "target_source": run.target_source,
                    "s1_id": source1_id,
                    "candidate_count": len(candidate_ids),
                    "has_candidates": bool(candidate_ids),
                    "zero_candidate_reason": (
                        "no_persisted_candidates" if not candidate_ids else None
                    ),
                }
                s1_line = json.dumps(
                    s1_record, sort_keys=True, separators=(",", ":")
                )
                manifest.write(s1_line + "\n")
                _digest_line(s1_digest, s1_line)
                for order, target_id in enumerate(candidate_ids):
                    record = {
                        "target_source": run.target_source,
                        "s1_id": source1_id,
                        "target_id": target_id,
                        "stage_id": stage_id,
                        "threshold": threshold,
                        "candidate_order": order,
                    }
                    line = json.dumps(
                        record, sort_keys=True, separators=(",", ":")
                    )
                    candidates.write(line + "\n")
                    _digest_line(candidate_digest, line)
                    candidate_rows += 1

    summary = CandidatePersistenceSummary(
        stage_id=stage_id,
        target_source=run.target_source,
        candidate_rows=candidate_rows,
        unique_candidate_keys=candidate_rows,
        validation_s1_count=len(validation_ids),
        zero_candidate_s1_count=zero_count,
        candidate_checksum=candidate_digest.hexdigest(),
        s1_manifest_checksum=s1_digest.hexdigest(),
    )
    manifest = {
        "schema_version": "m5.6.2-candidate-v1",
        "stage_id": stage_id,
        "target_source": run.target_source,
        "threshold": threshold,
        "split_fraction": split_fraction,
        "seed": seed,
        "candidate_rows": "candidates.jsonl",
        "s1_manifest": "s1_manifest.jsonl",
        "summary": summary.as_dict(),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def load_persisted_candidates(
    root: Path,
    stage_id: str,
    target_source: str,
) -> dict[str, set[str]]:
    """Load persisted rows into a candidate map for bounded replay checks."""
    path = _stage_dir(root, stage_id, target_source) / "candidates.jsonl"
    candidates: dict[str, set[str]] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            record = json.loads(line)
            if record["target_source"] != target_source:
                raise ValueError(f"Target source mismatch at line {line_number}")
            source1_id = record["s1_id"]
            target_id = record["target_id"]
            if target_id in candidates.setdefault(source1_id, set()):
                raise ValueError(f"Duplicate candidate at line {line_number}")
            candidates[source1_id].add(target_id)
    return candidates


def validate_persisted_candidates(
    root: Path,
    stage_id: str,
    target_source: str,
    validation_s1_ids: Iterable[str],
) -> CandidatePersistenceSummary:
    """Validate manifest counts, ordering, uniqueness, and replay equality."""
    output_dir = _stage_dir(root, stage_id, target_source)
    manifest = json.loads((output_dir / "manifest.json").read_text())
    expected_ids = sorted(set(validation_s1_ids))
    replayed = load_persisted_candidates(root, stage_id, target_source)
    candidate_rows = 0
    candidate_digest = hashlib.sha256()
    with (output_dir / "candidates.jsonl").open(encoding="utf-8") as handle:
        previous_key: tuple[str, str] | None = None
        for line_number, line in enumerate(handle, start=1):
            record = json.loads(line)
            key = (record["s1_id"], record["target_id"])
            if previous_key is not None and key < previous_key:
                raise ValueError(f"Candidate ordering mismatch at line {line_number}")
            previous_key = key
            _digest_line(candidate_digest, line.rstrip("\n"))
            candidate_rows += 1
    s1_rows: dict[str, int] = {}
    s1_digest = hashlib.sha256()
    with (output_dir / "s1_manifest.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            s1_rows[record["s1_id"]] = record["candidate_count"]
            _digest_line(s1_digest, line.rstrip("\n"))
    if sorted(s1_rows) != expected_ids:
        raise ValueError("S1 manifest does not match validation S1 universe")
    if any(s1_rows[s1_id] != len(replayed.get(s1_id, set())) for s1_id in expected_ids):
        raise ValueError("S1 manifest counts do not match candidate rows")
    expected_summary = manifest["summary"]
    summary = CandidatePersistenceSummary(
        stage_id=stage_id,
        target_source=target_source,
        candidate_rows=candidate_rows,
        unique_candidate_keys=len(
            {(source1_id, target_id) for source1_id, ids in replayed.items() for target_id in ids}
        ),
        validation_s1_count=len(expected_ids),
        zero_candidate_s1_count=sum(count == 0 for count in s1_rows.values()),
        candidate_checksum=candidate_digest.hexdigest(),
        s1_manifest_checksum=s1_digest.hexdigest(),
    )
    if summary.as_dict() != expected_summary:
        raise ValueError("Persisted summary does not match manifest")
    return summary
