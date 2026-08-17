from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar
from datetime import datetime
from enum import Enum


class BatchType(str, Enum):
    INITIAL = "INITIAL"
    INCREMENTAL = "INCREMENTAL"
    DELTA = "DELTA"
    CORRECTION = "CORRECTION"
    RECONCILIATION = "RECONCILIATION"
    REPLAY = "REPLAY"


class BatchStatus(str, Enum):
    RECEIVED = "RECEIVED"
    QUARANTINED = "QUARANTINED"
    VALIDATING = "VALIDATING"
    READY_FOR_PROFILING = "READY_FOR_PROFILING"
    PROFILING = "PROFILING"
    READY_FOR_MAPPING = "READY_FOR_MAPPING"
    PROCESSING = "PROCESSING"
    PARTIALLY_PROCESSED = "PARTIALLY_PROCESSED"
    RECONCILING = "RECONCILING"
    COMPLETED = "COMPLETED"
    FAILED_TECHNICAL = "FAILED_TECHNICAL"
    BLOCKED_GOVERNANCE = "BLOCKED_GOVERNANCE"
    SUPERSEDED = "SUPERSEDED"


@dataclass(slots=True)
class OnboardingBatch:
    id: str
    tenant_id: str
    scheme_id: str
    source_id: str
    batch_reference: str
    batch_type: BatchType
    source_extract_version: str
    snapshot_effective_at: datetime
    received_at: datetime
    source_control_totals: dict[str, int] | None = None
    records_received: int = 0
    records_processed: int = 0
    processing_statistics: dict[str, int] = field(default_factory=dict)
    policy_snapshot_id: str | None = None
    status: BatchStatus = BatchStatus.RECEIVED

    _allowed_transitions: ClassVar[dict[BatchStatus, tuple[BatchStatus, ...]]] = {
        BatchStatus.RECEIVED: (BatchStatus.QUARANTINED, BatchStatus.VALIDATING, BatchStatus.READY_FOR_PROFILING),
        BatchStatus.QUARANTINED: (BatchStatus.RECEIVED, BatchStatus.FAILED_TECHNICAL),
        BatchStatus.VALIDATING: (BatchStatus.READY_FOR_PROFILING, BatchStatus.BLOCKED_GOVERNANCE, BatchStatus.FAILED_TECHNICAL),
        BatchStatus.READY_FOR_PROFILING: (BatchStatus.PROFILING, BatchStatus.BLOCKED_GOVERNANCE),
        BatchStatus.PROFILING: (BatchStatus.READY_FOR_MAPPING, BatchStatus.BLOCKED_GOVERNANCE),
        BatchStatus.READY_FOR_MAPPING: (BatchStatus.PROCESSING, BatchStatus.BLOCKED_GOVERNANCE),
        BatchStatus.PROCESSING: (BatchStatus.PARTIALLY_PROCESSED, BatchStatus.RECONCILING, BatchStatus.COMPLETED, BatchStatus.BLOCKED_GOVERNANCE, BatchStatus.FAILED_TECHNICAL),
        BatchStatus.PARTIALLY_PROCESSED: (BatchStatus.PROCESSING, BatchStatus.RECONCILING, BatchStatus.COMPLETED, BatchStatus.BLOCKED_GOVERNANCE),
        BatchStatus.RECONCILING: (BatchStatus.COMPLETED, BatchStatus.BLOCKED_GOVERNANCE),
        BatchStatus.COMPLETED: (BatchStatus.SUPERSEDED,),
        BatchStatus.FAILED_TECHNICAL: (BatchStatus.RECEIVED,),
        BatchStatus.BLOCKED_GOVERNANCE: (BatchStatus.RECEIVED,),
        BatchStatus.SUPERSEDED: (),
    }

    def validate(self) -> None:
        if not self.id:
            raise ValueError("batch id is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if not self.scheme_id:
            raise ValueError("scheme_id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.batch_reference:
            raise ValueError("batch_reference is required")
        if not self.source_extract_version:
            raise ValueError("source_extract_version is required")
        if self.records_received < 0:
            raise ValueError("records_received cannot be negative")
        if self.records_processed < 0:
            raise ValueError("records_processed cannot be negative")
        if self.records_processed > self.records_received:
            raise ValueError("records_processed cannot exceed records_received")

    def can_transition_to(self, target_status: BatchStatus) -> bool:
        return target_status in self._allowed_transitions.get(self.status, ())

    def transition_to(self, target_status: BatchStatus) -> None:
        if not self.can_transition_to(target_status):
            raise ValueError(f"invalid batch lifecycle transition from {self.status} to {target_status}")
        self.status = target_status

    def mark_partial_processing(self) -> None:
        if self.status not in {BatchStatus.PROCESSING, BatchStatus.PARTIALLY_PROCESSED}:
            raise ValueError("partial processing is only valid while processing")
        self.status = BatchStatus.PARTIALLY_PROCESSED
