from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from data_onboarding.domain.reconciliation import (
    Discrepancy,
    DiscrepancySeverity,
    DiscrepancyType,
    ReconciliationReport,
    ReconciliationRule,
)


class ReconciliationService:
    def __init__(self) -> None:
        self._rules: dict[str, ReconciliationRule] = {}
        self._discrepancies: dict[str, Discrepancy] = {}
        self._reports: dict[str, ReconciliationReport] = {}

    def register_rule(self, rule: ReconciliationRule) -> ReconciliationRule:
        rule.validate()
        self._rules[rule.id] = rule
        return rule

    def get_rule(self, rule_id: str) -> ReconciliationRule | None:
        return self._rules.get(rule_id)

    def list_rules_for_source(self, source_id: str) -> list[ReconciliationRule]:
        return [r for r in self._rules.values() if r.source_id == source_id and r.enabled]

    def reconcile_records(
        self, batch_id: str, source_id: str, source_rows: list[dict], canonical_rows: list[dict], key_field: str = "id"
    ) -> list[Discrepancy]:
        discrepancies: list[Discrepancy] = []

        source_dict = {str(row.get(key_field)): row for row in source_rows}
        canonical_dict = {str(row.get(key_field)): row for row in canonical_rows}

        for canonical_key, canonical_row in canonical_dict.items():
            if canonical_key not in source_dict:
                discrepancy = Discrepancy(
                    id=f"disc-missing-{batch_id}-{canonical_key}",
                    batch_id=batch_id,
                    source_id=source_id,
                    discrepancy_type=DiscrepancyType.MISSING_RECORD,
                    severity=DiscrepancySeverity.HIGH,
                    entity_type="record",
                    entity_key=canonical_key,
                    description=f"Record {canonical_key} exists in canonical but not in source",
                    detected_at=datetime.now(UTC),
                )
                discrepancy.validate()
                discrepancies.append(discrepancy)
                self._discrepancies[discrepancy.id] = discrepancy

        for source_key, source_row in source_dict.items():
            if source_key not in canonical_dict:
                discrepancy = Discrepancy(
                    id=f"disc-extra-{batch_id}-{source_key}",
                    batch_id=batch_id,
                    source_id=source_id,
                    discrepancy_type=DiscrepancyType.EXTRA_RECORD,
                    severity=DiscrepancySeverity.MEDIUM,
                    entity_type="record",
                    entity_key=source_key,
                    description=f"Record {source_key} exists in source but not in canonical",
                    detected_at=datetime.now(UTC),
                )
                discrepancy.validate()
                discrepancies.append(discrepancy)
                self._discrepancies[discrepancy.id] = discrepancy
            else:
                canonical_row = canonical_dict[source_key]
                for field, canonical_value in canonical_row.items():
                    source_value = source_row.get(field)
                    if source_value != canonical_value:
                        discrepancy = Discrepancy(
                            id=f"disc-mismatch-{batch_id}-{source_key}-{field}",
                            batch_id=batch_id,
                            source_id=source_id,
                            discrepancy_type=DiscrepancyType.VALUE_MISMATCH,
                            severity=DiscrepancySeverity.HIGH,
                            entity_type="record",
                            entity_key=source_key,
                            field_name=field,
                            source_value=str(source_value),
                            expected_value=str(canonical_value),
                            description=f"Field '{field}' mismatch: got {source_value}, expected {canonical_value}",
                            detected_at=datetime.now(UTC),
                        )
                        discrepancy.validate()
                        discrepancies.append(discrepancy)
                        self._discrepancies[discrepancy.id] = discrepancy

        return discrepancies

    def reconcile_totals(
        self, batch_id: str, source_id: str, source_rows: list[dict], canonical_rows: list[dict], total_field: str
    ) -> list[Discrepancy]:
        discrepancies: list[Discrepancy] = []

        source_total = sum(float(row.get(total_field, 0)) for row in source_rows if row.get(total_field))
        canonical_total = sum(float(row.get(total_field, 0)) for row in canonical_rows if row.get(total_field))

        if abs(source_total - canonical_total) > 0.01:
            discrepancy = Discrepancy(
                id=f"disc-total-{batch_id}-{total_field}",
                batch_id=batch_id,
                source_id=source_id,
                discrepancy_type=DiscrepancyType.CALCULATION_ERROR,
                severity=DiscrepancySeverity.CRITICAL,
                entity_type="aggregate",
                entity_key=total_field,
                field_name=total_field,
                source_value=str(source_total),
                expected_value=str(canonical_total),
                description=f"Total mismatch on field '{total_field}': source={source_total}, canonical={canonical_total}",
                detected_at=datetime.now(UTC),
            )
            discrepancy.validate()
            discrepancies.append(discrepancy)
            self._discrepancies[discrepancy.id] = discrepancy

        return discrepancies

    def generate_report(self, batch_id: str, source_id: str, discrepancies: list[Discrepancy]) -> ReconciliationReport:
        by_severity = defaultdict(int)
        for disc in discrepancies:
            by_severity[disc.severity] += 1

        critical_count = by_severity.get(DiscrepancySeverity.CRITICAL, 0)
        passed = len(discrepancies) == 0  # Only pass if there are zero discrepancies

        report = ReconciliationReport(
            id=f"report-{batch_id}",
            batch_id=batch_id,
            source_id=source_id,
            total_records_compared=len(discrepancies),
            total_discrepancies_found=len(discrepancies),
            critical_count=critical_count,
            high_count=by_severity.get(DiscrepancySeverity.HIGH, 0),
            medium_count=by_severity.get(DiscrepancySeverity.MEDIUM, 0),
            low_count=by_severity.get(DiscrepancySeverity.LOW, 0),
            reconciliation_percentage=100.0 - (len(discrepancies) / max(1, len(discrepancies) + 100) * 100),
            discrepancy_ids=[d.id for d in discrepancies],
            generated_at=datetime.now(UTC),
            passed=passed,
        )
        report.validate()
        self._reports[report.id] = report
        return report

    def get_report(self, report_id: str) -> ReconciliationReport | None:
        return self._reports.get(report_id)

    def list_reports_for_batch(self, batch_id: str) -> list[ReconciliationReport]:
        return [r for r in self._reports.values() if r.batch_id == batch_id]

    def get_discrepancy(self, discrepancy_id: str) -> Discrepancy | None:
        return self._discrepancies.get(discrepancy_id)

    def list_discrepancies_for_batch(self, batch_id: str) -> list[Discrepancy]:
        return [d for d in self._discrepancies.values() if d.batch_id == batch_id]

    def mark_discrepancy_resolved(self, discrepancy_id: str, resolution_notes: str | None = None) -> Discrepancy | None:
        disc = self._discrepancies.get(discrepancy_id)
        if disc:
            disc.resolved = True
            disc.resolution_notes = resolution_notes
        return disc
