from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class SourceStatus(str, Enum):
    REGISTERED = "REGISTERED"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


@dataclass(slots=True)
class OnboardingSource:
    id: str
    tenant_id: str
    scheme_id: str
    source_name: str
    source_type: str
    source_system_product: str
    source_system_version: str
    ceding_administrator: str | None = None
    owner_contact: str | None = None
    delivery_channel: str | None = None
    schema_version: str | None = None
    timezone: str = "UTC"
    encoding: str = "utf-8"
    data_classification: str = "internal"
    expected_extract_type: str = "csv"
    source_authority_profile: str | None = None
    known_defect_profile: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    status: SourceStatus = SourceStatus.REGISTERED
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("source id is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if not self.scheme_id:
            raise ValueError("scheme_id is required")
        if not self.source_name:
            raise ValueError("source_name is required")
        if not self.source_type:
            raise ValueError("source_type is required")
        if not self.source_system_product:
            raise ValueError("source_system_product is required")
        if not self.source_system_version:
            raise ValueError("source_system_version is required")
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValueError("effective_from cannot be later than effective_to")

    def is_active(self) -> bool:
        return self.status == SourceStatus.ACTIVE
