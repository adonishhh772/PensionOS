from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

import pytest

from data_onboarding.domain.batch import BatchStatus, BatchType, OnboardingBatch
from data_onboarding.domain.source import OnboardingSource
from data_onboarding.repositories.in_memory import (
    InMemoryAssetRepository,
    InMemoryBatchRepository,
    InMemoryMalwareScanner,
    InMemoryObjectStore,
    InMemorySourceRepository,
)
from data_onboarding.services.intake import IntakeService


def make_source() -> OnboardingSource:
    return OnboardingSource(
        id="src-1",
        tenant_id="tenant-1",
        scheme_id="scheme-1",
        source_name="Payroll export",
        source_type="PAYROLL",
        source_system_product="PayrollX",
        source_system_version="1.0",
    )


def make_batch(source: OnboardingSource, batch_id: str = "batch-1") -> OnboardingBatch:
    now = datetime.now(UTC)
    return OnboardingBatch(
        id=batch_id,
        tenant_id=source.tenant_id,
        scheme_id=source.scheme_id,
        source_id=source.id,
        batch_reference="batch-ref-1",
        batch_type=BatchType.INITIAL,
        source_extract_version="v1",
        snapshot_effective_at=now,
        received_at=now,
    )


def test_clean_asset_ingest():
    store = InMemoryObjectStore()
    assets = InMemoryAssetRepository()
    scanner = InMemoryMalwareScanner()

    intake = IntakeService(assets, store, scanner)
    content = b"name,age\nAlice,30"
    saved = intake.ingest_asset("src-1", "batch-1", "file.csv", content, "text/csv")
    assert saved.metadata.get("malware_status") == "CLEAN"
    assert saved.content_hash == sha256(content).hexdigest()
    assert assets.get_by_id(saved.id) is not None


def test_malware_quarantine():
    source_repo = InMemorySourceRepository()
    batch_repo = InMemoryBatchRepository()
    source = source_repo.save(make_source())
    batch = batch_repo.save(make_batch(source))

    intake = IntakeService(
        InMemoryAssetRepository(),
        InMemoryObjectStore(),
        InMemoryMalwareScanner(),
        source_repo,
        batch_repo,
    )
    saved = intake.ingest_asset("src-1", "batch-1", "evil.bin", b"MALWARE payload", "application/octet-stream")
    assert saved.metadata.get("malware_status") == "INFECTED"
    assert saved.metadata.get("quarantine") == "true"
    assert batch.status == BatchStatus.QUARANTINED


def test_duplicate_asset_delivery_is_idempotent_for_batch_and_content_hash():
    assets = InMemoryAssetRepository()
    intake = IntakeService(assets, InMemoryObjectStore(), InMemoryMalwareScanner())

    first = intake.ingest_asset("src-1", "batch-1", "file.csv", b"same content", "text/csv")
    second = intake.ingest_asset("src-1", "batch-1", "file.csv", b"same content", "text/csv")

    assert second.id == first.id
    assert assets.list_for_batch("batch-1") == [first]


def test_governed_intake_rejects_unknown_source():
    intake = IntakeService(
        InMemoryAssetRepository(),
        InMemoryObjectStore(),
        InMemoryMalwareScanner(),
        InMemorySourceRepository(),
        InMemoryBatchRepository(),
    )

    with pytest.raises(ValueError, match="source does not exist"):
        intake.ingest_asset("missing-source", "batch-1", "file.csv", b"content", "text/csv")


def test_governed_intake_rejects_batch_source_mismatch():
    source_repo = InMemorySourceRepository()
    batch_repo = InMemoryBatchRepository()
    source = source_repo.save(make_source())
    other_source = make_source()
    other_source.id = "src-2"
    source_repo.save(other_source)
    batch_repo.save(make_batch(source))

    intake = IntakeService(
        InMemoryAssetRepository(),
        InMemoryObjectStore(),
        InMemoryMalwareScanner(),
        source_repo,
        batch_repo,
    )

    with pytest.raises(ValueError, match="batch source_id must match source_id"):
        intake.ingest_asset(other_source.id, "batch-1", "file.csv", b"content", "text/csv")
