from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from data_onboarding.domain.data_state import DataState


@dataclass(slots=True)
class ProfileObservation:
    id: str
    field_name: str
    observed_type: str
    data_state: DataState
    total_count: int = 0
    provided_count: int = 0
    missing_count: int = 0
    null_count: int = 0
    blank_count: int = 0
    distinct_count: int = 0
    null_ratio: float = 0.0
    sample_values: list[str] = field(default_factory=list)
    observed_patterns: list[str] = field(default_factory=list)
    notes: str | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("observation id is required")
        if not self.field_name:
            raise ValueError("field_name is required")
        if not self.observed_type:
            raise ValueError("observed_type is required")
        if self.total_count < 0:
            raise ValueError("total_count cannot be negative")
        if self.provided_count < 0:
            raise ValueError("provided_count cannot be negative")
        if self.missing_count < 0:
            raise ValueError("missing_count cannot be negative")
        if self.null_count < 0:
            raise ValueError("null_count cannot be negative")
        if self.blank_count < 0:
            raise ValueError("blank_count cannot be negative")
        if not 0.0 <= self.null_ratio <= 1.0:
            raise ValueError("null_ratio must be between 0.0 and 1.0")


@dataclass(slots=True)
class DataProfile:
    id: str
    batch_id: str
    source_id: str
    total_records: int
    field_observations: list[ProfileObservation] = field(default_factory=list)
    generated_at: datetime | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("profile id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if self.total_records < 0:
            raise ValueError("total_records cannot be negative")


@dataclass(slots=True)
class OnboardingEntity:
    id: str
    entity_name: str
    record_count: int
    data_state: DataState = DataState.KNOWN

    def validate(self) -> None:
        if not self.id:
            raise ValueError("entity id is required")
        if not self.entity_name:
            raise ValueError("entity_name is required")
        if self.record_count < 0:
            raise ValueError("record_count cannot be negative")


@dataclass(slots=True)
class OnboardingField:
    id: str
    entity_id: str
    field_name: str
    observed_type: str
    null_ratio: float = 0.0
    data_state: DataState = DataState.KNOWN
    sample_values: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("field id is required")
        if not self.entity_id:
            raise ValueError("entity_id is required")
        if not self.field_name:
            raise ValueError("field_name is required")
        if not 0.0 <= self.null_ratio <= 1.0:
            raise ValueError("null_ratio must be between 0.0 and 1.0")


@dataclass(slots=True)
class OnboardingRelationship:
    id: str
    parent_entity_id: str
    child_entity_id: str
    relationship_name: str
    cardinality: str = "one_to_many"

    def validate(self) -> None:
        if not self.id:
            raise ValueError("relationship id is required")
        if not self.parent_entity_id:
            raise ValueError("parent_entity_id is required")
        if not self.child_entity_id:
            raise ValueError("child_entity_id is required")
        if not self.relationship_name:
            raise ValueError("relationship_name is required")


@dataclass(slots=True)
class ProfilingResult:
    id: str
    batch_id: str
    record_count: int
    field_stats: dict[str, dict] = field(default_factory=dict)
    profile_observations: list[ProfileObservation] = field(default_factory=list)
    created_at: datetime | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("profiling id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if self.record_count < 0:
            raise ValueError("record_count cannot be negative")
