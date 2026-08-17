from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MappingApprovalStatus(str, Enum):
    PENDING = "PENDING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class MappingPackStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


class MappingOverlayLevel(str, Enum):
    BASE = "BASE"
    SOURCE_SYSTEM = "SOURCE_SYSTEM"
    CEDING_ADMINISTRATOR = "CEDING_ADMINISTRATOR"
    SCHEME = "SCHEME"
    SECTION = "SECTION"
    BATCH_EXCEPTION = "BATCH_EXCEPTION"


@dataclass(slots=True)
class FieldMappingRule:
    source_field: str
    target_field: str
    source_type: str
    target_domain: str
    materiality: str = "standard"
    derivation_rule: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_field:
            raise ValueError("source_field is required")
        if not self.target_field:
            raise ValueError("target_field is required")
        if not self.source_type:
            raise ValueError("source_type is required")
        if not self.target_domain:
            raise ValueError("target_domain is required")


@dataclass(slots=True)
class CodeTranslationRule:
    source_code: str
    target_code: str
    source_field: str
    target_field: str
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_code:
            raise ValueError("source_code is required")
        if not self.target_code:
            raise ValueError("target_code is required")
        if not self.source_field:
            raise ValueError("source_field is required")
        if not self.target_field:
            raise ValueError("target_field is required")


@dataclass(slots=True)
class RelationshipMappingRule:
    parent_entity: str
    child_entity: str
    relationship_name: str
    source_type: str
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.parent_entity:
            raise ValueError("parent_entity is required")
        if not self.child_entity:
            raise ValueError("child_entity is required")
        if not self.relationship_name:
            raise ValueError("relationship_name is required")
        if not self.source_type:
            raise ValueError("source_type is required")


@dataclass(slots=True)
class DerivationRule:
    source_field: str
    target_field: str
    formula: str
    source_type: str
    derivation_method_version: str = "v1"
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source_field:
            raise ValueError("source_field is required")
        if not self.target_field:
            raise ValueError("target_field is required")
        if not self.formula:
            raise ValueError("formula is required")
        if not self.source_type:
            raise ValueError("source_type is required")
        if not self.derivation_method_version:
            raise ValueError("derivation_method_version is required")
        if not self.evidence_refs:
            raise ValueError("derivation rules require source evidence refs")


@dataclass(slots=True)
class MappingTestCase:
    id: str
    source_record: dict[str, object]
    expected_target_record: dict[str, object]
    description: str | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("test case id is required")
        if not self.source_record:
            raise ValueError("source_record is required")
        if not self.expected_target_record:
            raise ValueError("expected_target_record is required")


@dataclass(slots=True)
class MappingApprovalPolicy:
    id: str
    source_type: str
    field_domain: str
    requires_human_approval: bool = True
    min_confidence: float | None = None
    required_tests: list[str] = field(default_factory=list)
    human_roles: list[str] = field(default_factory=list)
    materiality: str = "standard"
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("approval policy id is required")
        if not self.source_type:
            raise ValueError("source_type is required")
        if not self.field_domain:
            raise ValueError("field_domain is required")
        if self.min_confidence is not None and not (0.0 <= self.min_confidence <= 1.0):
            raise ValueError("min_confidence must be between 0.0 and 1.0")

    def requires_review(self, confidence: float | None = None, material: bool = False) -> bool:
        if material:
            return True
        if self.requires_human_approval:
            return True
        if self.min_confidence is not None and confidence is not None:
            return confidence < self.min_confidence
        return False


@dataclass(slots=True)
class MappingApproval:
    id: str
    mapping_pack_id: str
    source_field: str
    target_field: str
    status: MappingApprovalStatus = MappingApprovalStatus.PENDING
    approved_by: str | None = None
    rationale: str | None = None
    reviewed_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("approval id is required")
        if not self.mapping_pack_id:
            raise ValueError("mapping_pack_id is required")
        if not self.source_field:
            raise ValueError("source_field is required")
        if not self.target_field:
            raise ValueError("target_field is required")


@dataclass(slots=True)
class MappingSuggestion:
    id: str
    mapping_pack_id: str
    source_field: str
    suggested_target_field: str
    confidence: float
    evidence: dict[str, str] | None = None
    created_at: datetime | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("suggestion id is required")
        if not self.mapping_pack_id:
            raise ValueError("mapping_pack_id is required")
        if not self.source_field:
            raise ValueError("source_field is required")
        if not self.suggested_target_field:
            raise ValueError("suggested_target_field is required")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(slots=True)
class MappingPack:
    id: str
    source_type: str
    version: str
    target_contract_version: str = "v1"
    status: MappingPackStatus = MappingPackStatus.DRAFT
    overlay_level: MappingOverlayLevel = MappingOverlayLevel.SOURCE_SYSTEM
    supersedes_pack_id: str | None = None
    mappings: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    field_rules: list[FieldMappingRule] = field(default_factory=list)
    code_rules: list[CodeTranslationRule] = field(default_factory=list)
    relationship_rules: list[RelationshipMappingRule] = field(default_factory=list)
    derivation_rules: list[DerivationRule] = field(default_factory=list)
    test_cases: list[MappingTestCase] = field(default_factory=list)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("pack id is required")
        if not self.source_type:
            raise ValueError("source_type is required")
        if not self.version:
            raise ValueError("version is required")
        if not self.target_contract_version:
            raise ValueError("target_contract_version is required")
        if self.status == MappingPackStatus.SUPERSEDED and not self.supersedes_pack_id:
            raise ValueError("superseded mapping pack must reference supersedes_pack_id")
        for source_field, target_field in self.mappings.items():
            if not source_field:
                raise ValueError("mapping source_field is required")
            self._validate_target_field(target_field)
        for rule in self.field_rules:
            rule.validate()
            self._validate_target_field(rule.target_field)
        for rule in self.code_rules:
            rule.validate()
            self._validate_target_field(rule.target_field)
        for rule in self.derivation_rules:
            rule.validate()
            self._validate_target_field(rule.target_field)
        for test_case in self.test_cases:
            test_case.validate()

    def add_mapping(self, source_field: str, target_field: str) -> None:
        if not source_field:
            raise ValueError("source_field is required")
        self._validate_target_field(target_field)
        self.mappings[source_field] = target_field

    def target_for(self, source_field: str) -> str | None:
        return self.mappings.get(source_field)

    def activate(self) -> None:
        self.validate()
        self.status = MappingPackStatus.ACTIVE

    def supersede(self, replacement_pack_id: str) -> None:
        if not replacement_pack_id:
            raise ValueError("replacement_pack_id is required")
        self.status = MappingPackStatus.SUPERSEDED
        self.supersedes_pack_id = replacement_pack_id

    @staticmethod
    def _validate_target_field(target_field: str) -> None:
        if not target_field:
            raise ValueError("target_field is required")
        if "." not in target_field:
            raise ValueError("target_field must be a canonical contract path")
