from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class AuthorityClass(str, Enum):
    PRIMARY = "PRIMARY"
    SUPPORTING = "SUPPORTING"
    CORROBORATIVE = "CORROBORATIVE"


@dataclass(slots=True)
class SourceAuthorityPolicy:
    id: str
    version: str
    field_domain_group: str
    source_type: str
    authority_class: AuthorityClass
    applicability_conditions: dict[str, str] | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    known_defect_rules: dict[str, str] | None = None
    tie_break_review_policy: str | None = None
    evidence_requirements: list[str] | None = None

    def validate(self) -> None:
        if not self.id:
            raise ValueError("policy id is required")
        if not self.version:
            raise ValueError("version is required")
        if not self.field_domain_group:
            raise ValueError("field_domain_group is required")
        if not self.source_type:
            raise ValueError("source_type is required")
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError("effective_from cannot be later than effective_to")
