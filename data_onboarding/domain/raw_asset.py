from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class RawOnboardingAsset:
    id: str
    source_id: str
    batch_id: str
    object_uri: str
    original_filename: str
    mime_type: str
    content_length: int
    content_hash: str
    encryption_status: str | None = None
    uploaded_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id:
            raise ValueError("asset id is required")
        if not self.source_id:
            raise ValueError("source_id is required")
        if not self.batch_id:
            raise ValueError("batch_id is required")
        if not self.object_uri:
            raise ValueError("object_uri is required")
        if self.content_length < 0:
            raise ValueError("content_length cannot be negative")