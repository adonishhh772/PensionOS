from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DiscrepancyType(str, Enum):
    VALUE_MISMATCH = "VALUE_MISMATCH"
    MISSING_RECORD = "MISSING_RECORD"
    EXTRA_RECORD = "EXTRA_RECORD"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    REFERENCE_BROKEN = "REFERENCE_BROKEN"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    DATE_INCONSISTENCY = "DATE_INCONSISTENCY"


class DiscrepancySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(slots=True)
class ReconciliationRule:
    id: str
    source_id: str
    rule_name: str
    entity_type: str
    key_fields: list[str] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    validation_logic: str | None = None
    tolerance_percentage: float = 0.0
    enabled: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("rule id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.rule_name:
            raise ValueError("rule_name is required")
        if not self.entity_type:
            raise ValueError("entity_type is required")


@dataclass(slots=True)
class Discrepancy:
    id: str
    batch_id: str
    source_id: str
    discrepancy_type: DiscrepancyType
    severity: DiscrepancySeverity
    entity_type: str
    entity_key: str
    field_name: str | None = None
    source_value: str | None = None
    expected_value: str | None = None
    description: str | None = None
    detected_at: datetime | None = None
    resolved: bool = False
    resolution_notes: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("discrepancy id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.entity_type:
            raise ValueError("entity_type is required")
        if not self.entity_key:
            raise ValueError("entity_key is required")


@dataclass(slots=True)
class ReconciliationReport:
    id: str
    batch_id: str
    source_id: str
    total_records_compared: int
    total_discrepancies_found: int
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    reconciliation_percentage: float = 100.0
    discrepancy_ids: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
    passed: bool = False
    notes: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("report id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        total_by_severity = self.critical_count + self.high_count + self.medium_count + self.low_count
        if total_by_severity != self.total_discrepancies_found:
            raise ValueError("sum of severity counts must equal total discrepancies found")

    def is_clean(self) -> bool:
        return self.total_discrepancies_found == 0 and self.passed

    def impact_summary(self) -> str:
        if self.critical_count > 0:
            return "BLOCKING"
        if self.high_count > 5:
            return "SIGNIFICANT"
        if self.medium_count > 10:
            return "NOTABLE"
        return "MINOR"
