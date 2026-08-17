from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExceptionSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ExceptionCategory(str, Enum):
    DATA_QUALITY = "DATA_QUALITY"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    REFERENCE_INTEGRITY = "REFERENCE_INTEGRITY"
    COMPLETENESS = "COMPLETENESS"
    ACCURACY = "ACCURACY"
    CONSISTENCY = "CONSISTENCY"
    DUPLICATE = "DUPLICATE"
    MAPPING_ISSUE = "MAPPING_ISSUE"
    TRANSFORMATION_ERROR = "TRANSFORMATION_ERROR"


class ExceptionResolutionStatus(str, Enum):
    DETECTED = "DETECTED"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    ARCHIVED = "ARCHIVED"


@dataclass(slots=True)
class DataQualityIssue:
    id: str
    batch_id: str
    source_id: str
    field_name: str
    entity_name: str
    record_id: str | None = None
    issue_type: str = "null_value"
    observed_value: str | None = None
    expected_pattern: str | None = None
    sample_values: list[str] = field(default_factory=list)
    detected_at: datetime | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("issue id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.field_name:
            raise ValueError("field_name is required")


@dataclass(slots=True)
class OnboardingException:
    id: str
    batch_id: str
    source_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    description: str
    affected_records: int = 0
    affected_fields: list[str] = field(default_factory=list)
    root_cause: str | None = None
    resolution_status: ExceptionResolutionStatus = ExceptionResolutionStatus.DETECTED
    assigned_to: str | None = None
    resolution_notes: str | None = None
    detected_at: datetime | None = None
    resolved_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    related_issues: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("exception id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.description:
            raise ValueError("description is required")

    def is_critical(self) -> bool:
        return self.severity == ExceptionSeverity.CRITICAL or self.affected_records > 100


@dataclass(slots=True)
class ExceptionCluster:
    id: str
    batch_id: str
    root_cause: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    member_exceptions: list[str] = field(default_factory=list)
    affected_record_count: int = 0
    resolution_strategy: str | None = None
    resolution_status: ExceptionResolutionStatus = ExceptionResolutionStatus.DETECTED
    assigned_to: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("cluster id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.root_cause:
            raise ValueError("root_cause is required")
        if not self.member_exceptions:
            raise ValueError("cluster must have at least one member exception")

    def add_member(self, exception_id: str) -> None:
        if exception_id not in self.member_exceptions:
            self.member_exceptions.append(exception_id)

    def is_actionable(self) -> bool:
        return len(self.member_exceptions) >= 3 or self.severity == ExceptionSeverity.CRITICAL
