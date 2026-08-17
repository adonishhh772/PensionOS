from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Optional
from uuid import uuid4

from data_onboarding.domain.batch import BatchStatus
from data_onboarding.domain.raw_asset import RawOnboardingAsset
from data_onboarding.repositories.ports import (
    AssetRepositoryPort,
    BatchRepositoryPort,
    MalwareScannerPort,
    ObjectStorePort,
    SourceRepositoryPort,
)


class IntakeService:
    def __init__(
        self,
        asset_repo: AssetRepositoryPort,
        object_store: ObjectStorePort,
        scanner: MalwareScannerPort,
        source_repo: SourceRepositoryPort | None = None,
        batch_repo: BatchRepositoryPort | None = None,
    ) -> None:
        self.asset_repo = asset_repo
        self.object_store = object_store
        self.scanner = scanner
        self.source_repo = source_repo
        self.batch_repo = batch_repo

    def ingest_asset(self, source_id: str, batch_id: str, filename: str, content: bytes, mime_type: str, retention_policy: Optional[str] = None) -> RawOnboardingAsset:
        if not source_id:
            raise ValueError("source_id is required")
        if not batch_id:
            raise ValueError("batch_id is required")
        if not filename:
            raise ValueError("filename is required")
        if not mime_type:
            raise ValueError("mime_type is required")
        if not content:
            raise ValueError("asset content cannot be empty")

        if self.source_repo is not None and self.source_repo.get_by_id(source_id) is None:
            raise ValueError("source does not exist")

        batch = self.batch_repo.get_by_id(batch_id) if self.batch_repo is not None else None
        if self.batch_repo is not None and batch is None:
            raise ValueError("batch does not exist")
        if batch is not None:
            if batch.source_id != source_id:
                raise ValueError("batch source_id must match source_id")
            if batch.status == BatchStatus.SUPERSEDED:
                raise ValueError("cannot ingest asset into superseded batch")

        content_length = len(content)
        content_hash = sha256(content).hexdigest()

        duplicate = self.asset_repo.get_by_batch_and_hash(batch_id, content_hash)
        if duplicate is not None:
            return duplicate

        scan_result = self.scanner.scan(content)
        malware_status = "INFECTED" if scan_result.get("malware") else "CLEAN"
        object_uri = self.object_store.upload(content, filename, mime_type)

        asset = RawOnboardingAsset(
            id=f"asset-{uuid4()}",
            source_id=source_id,
            batch_id=batch_id,
            object_uri=object_uri,
            original_filename=filename,
            mime_type=mime_type,
            content_length=content_length,
            content_hash=content_hash,
            encryption_status=None,
            uploaded_at=datetime.now(UTC),
            metadata={
                "malware_status": malware_status,
                "scanner_details": scan_result.get("details", ""),
            },
        )
        if retention_policy is not None:
            asset.metadata["retention_policy"] = retention_policy

        if scan_result.get("malware"):
            asset.metadata["quarantine"] = "true"
            if batch is not None and batch.can_transition_to(BatchStatus.QUARANTINED):
                batch.transition_to(BatchStatus.QUARANTINED)
                self.batch_repo.save(batch)

        asset.validate()
        saved = self.asset_repo.save(asset)
        return saved
