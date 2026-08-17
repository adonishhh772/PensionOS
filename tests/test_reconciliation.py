from __future__ import annotations

from datetime import UTC, datetime

from data_onboarding.domain.batch import OnboardingBatch, BatchType
from data_onboarding.domain.reconciliation import DiscrepancyType, DiscrepancySeverity, ReconciliationRule
from data_onboarding.domain.source import OnboardingSource
from data_onboarding.services.reconciliation import ReconciliationService


def make_source() -> OnboardingSource:
    return OnboardingSource(
        id="src-rec",
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
        id="batch-rec",
        tenant_id=source.tenant_id,
        scheme_id=source.scheme_id,
        source_id=source.id,
        batch_reference="ref-rec",
        batch_type=BatchType.INITIAL,
        source_extract_version="2024.1",
        snapshot_effective_at=now,
        received_at=now,
        records_received=10,
    )


def test_reconciliation_rule_register():
    service = ReconciliationService()
    rule = ReconciliationRule(
        id="rule-1",
        source_id="src-1",
        rule_name="Member records exist",
        entity_type="member",
        key_fields=["member_id"],
        required_fields=["name", "dob"],
    )

    registered = service.register_rule(rule)
    assert registered.id == "rule-1"

    retrieved = service.get_rule("rule-1")
    assert retrieved is not None
    assert retrieved.rule_name == "Member records exist"


def test_reconciliation_missing_records():
    service = ReconciliationService()
    source = make_source()
    batch = make_batch(source)

    source_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
        {"id": "2", "name": "Bob", "salary": 95000},
    ]

    canonical_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
        {"id": "2", "name": "Bob", "salary": 95000},
        {"id": "3", "name": "Carol", "salary": 110000},  # Missing from source
    ]

    discrepancies = service.reconcile_records(batch.id, source.id, source_rows, canonical_rows, key_field="id")
    assert len(discrepancies) > 0

    missing_disc = next((d for d in discrepancies if d.discrepancy_type == DiscrepancyType.MISSING_RECORD), None)
    assert missing_disc is not None
    assert missing_disc.severity == DiscrepancySeverity.HIGH


def test_reconciliation_value_mismatch():
    service = ReconciliationService()
    source = make_source()
    batch = make_batch(source)

    source_rows = [
        {"id": "1", "name": "Alice", "salary": 105000},  # Mismatch
    ]

    canonical_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
    ]

    discrepancies = service.reconcile_records(batch.id, source.id, source_rows, canonical_rows, key_field="id")
    assert len(discrepancies) > 0

    mismatch_disc = next((d for d in discrepancies if d.discrepancy_type == DiscrepancyType.VALUE_MISMATCH), None)
    assert mismatch_disc is not None
    assert mismatch_disc.field_name == "salary"
    assert mismatch_disc.source_value == "105000"
    assert mismatch_disc.expected_value == "100000"


def test_reconciliation_total_mismatch():
    service = ReconciliationService()
    source = make_source()
    batch = make_batch(source)

    source_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
        {"id": "2", "name": "Bob", "salary": 90000},  # 190000 total
    ]

    canonical_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
        {"id": "2", "name": "Bob", "salary": 95000},  # 195000 total
    ]

    discrepancies = service.reconcile_totals(batch.id, source.id, source_rows, canonical_rows, "salary")
    assert len(discrepancies) > 0

    total_disc = discrepancies[0]
    assert total_disc.discrepancy_type == DiscrepancyType.CALCULATION_ERROR
    assert total_disc.severity == DiscrepancySeverity.CRITICAL


def test_reconciliation_report_generation():
    service = ReconciliationService()
    source = make_source()
    batch = make_batch(source)

    source_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
    ]

    canonical_rows = [
        {"id": "1", "name": "Alice", "salary": 100000},
        {"id": "2", "name": "Bob", "salary": 95000},
    ]

    discrepancies = service.reconcile_records(batch.id, source.id, source_rows, canonical_rows, key_field="id")
    report = service.generate_report(batch.id, source.id, discrepancies)

    assert report.batch_id == batch.id
    assert report.total_discrepancies_found > 0
    assert report.impact_summary() in ("BLOCKING", "SIGNIFICANT", "NOTABLE", "MINOR")
    assert not report.passed  # Has discrepancies


def test_reconciliation_report_clean_pass():
    service = ReconciliationService()
    source = make_source()
    batch = make_batch(source)

    source_rows = [{"id": "1", "name": "Alice"}]
    canonical_rows = [{"id": "1", "name": "Alice"}]

    discrepancies = service.reconcile_records(batch.id, source.id, source_rows, canonical_rows)
    report = service.generate_report(batch.id, source.id, discrepancies)

    assert report.total_discrepancies_found == 0
    assert report.passed
    assert report.is_clean()


def test_reconciliation_discrepancy_resolution():
    service = ReconciliationService()
    source = make_source()
    batch = make_batch(source)

    source_rows = [{"id": "1", "name": "Alice"}]
    canonical_rows = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

    discrepancies = service.reconcile_records(batch.id, source.id, source_rows, canonical_rows)
    assert len(discrepancies) > 0

    disc = discrepancies[0]
    assert not disc.resolved

    resolved = service.mark_discrepancy_resolved(disc.id, "Accepted: record is archived")
    assert resolved is not None
    assert resolved.resolved
    assert resolved.resolution_notes == "Accepted: record is archived"
