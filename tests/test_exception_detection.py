from __future__ import annotations

from datetime import UTC, datetime

from data_onboarding.domain.batch import OnboardingBatch, BatchType
from data_onboarding.domain.exception import ExceptionCategory, ExceptionSeverity, ExceptionResolutionStatus
from data_onboarding.domain.source import OnboardingSource
from data_onboarding.repositories.in_memory import InMemoryExceptionRepository
from data_onboarding.services.exception_detection import ExceptionDetectionService


def make_source() -> OnboardingSource:
    return OnboardingSource(
        id="src-exc",
        tenant_id="t1",
        scheme_id="sch-1",
        source_name="TestSource",
        source_type="payroll",
        source_system_product="ADP",
        source_system_version="2024.1",
    )


def make_batch(source: OnboardingSource) -> OnboardingBatch:
    now = datetime.now(UTC)
    return OnboardingBatch(
        id="batch-exc",
        tenant_id=source.tenant_id,
        scheme_id=source.scheme_id,
        source_id=source.id,
        batch_reference="ref-exc",
        batch_type=BatchType.INITIAL,
        source_extract_version="2024.1",
        snapshot_effective_at=now,
        received_at=now,
        records_received=10,
    )


def test_exception_detection_nulls():
    service = ExceptionDetectionService()
    source = make_source()
    batch = make_batch(source)

    rows = [
        {"name": "Alice", "salary": 100000},
        {"name": "Bob", "salary": None},
        {"name": None, "salary": 95000},
        {"name": None, "salary": None},
        {"name": "Carol", "salary": 110000},
    ]

    exceptions = service.detect_nulls(batch.id, source.id, rows, threshold=0.2)
    assert len(exceptions) > 0
    name_exc = next((e for e in exceptions if "name" in e.affected_fields), None)
    assert name_exc is not None
    assert name_exc.category == ExceptionCategory.COMPLETENESS
    assert name_exc.affected_records == 2


def test_exception_detection_duplicates():
    service = ExceptionDetectionService()
    source = make_source()
    batch = make_batch(source)

    rows = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
        {"id": "1", "name": "Alice"},
    ]

    exceptions = service.detect_duplicates(batch.id, source.id, rows, key_fields=["id"])
    assert len(exceptions) > 0
    dup_exc = exceptions[0]
    assert dup_exc.category == ExceptionCategory.DUPLICATE
    assert dup_exc.severity == ExceptionSeverity.MEDIUM


def test_exception_clustering():
    service = ExceptionDetectionService()
    source = make_source()
    batch = make_batch(source)

    rows = [
        {"name": None, "salary": 100000},
        {"name": None, "salary": 110000},
        {"name": "Carol", "salary": None},
        {"name": "Dave", "salary": None},
    ]

    exceptions = service.detect_nulls(batch.id, source.id, rows, threshold=0.1)
    assert len(exceptions) > 0

    clusters = service.cluster_exceptions(batch.id, exceptions)
    assert len(clusters) > 0

    cluster = clusters[0]
    assert cluster.category == ExceptionCategory.COMPLETENESS
    assert len(cluster.member_exceptions) >= 1


def test_exception_resolution():
    service = ExceptionDetectionService()
    source = make_source()
    batch = make_batch(source)

    rows = [{"name": None, "salary": 100000}]
    exceptions = service.detect_nulls(batch.id, source.id, rows, threshold=0.0)

    assert len(exceptions) > 0
    exc = exceptions[0]
    assert exc.resolution_status == ExceptionResolutionStatus.DETECTED

    resolved = service.mark_exception_resolved(exc.id, resolution_notes="Accepted risk")
    assert resolved is not None
    assert resolved.resolution_status == ExceptionResolutionStatus.RESOLVED
    assert resolved.resolution_notes == "Accepted risk"
