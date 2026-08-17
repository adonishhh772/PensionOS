from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, date
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data_onboarding.domain.source import OnboardingSource
from data_onboarding.domain.batch import OnboardingBatch, BatchType
from data_onboarding.domain.mapping import MappingPack, MappingSuggestion
from data_onboarding.repositories.in_memory import (
    InMemorySourceRepository,
    InMemoryBatchRepository,
    InMemoryMappingRepository,
)
from data_onboarding.repositories.in_memory import InMemoryObjectStore, InMemoryMalwareScanner, InMemoryAssetRepository
from data_onboarding.services.intake import IntakeService
from data_onboarding.services.source_registry import SourceRegistryService
from data_onboarding.services.mapping_pack import MappingService

app = FastAPI(title="PensionOS Data Onboarding - Backend (scaffold)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# instantiate in-memory adapters and services (development/demo only)
src_repo = InMemorySourceRepository()
batch_repo = InMemoryBatchRepository()
mapping_repo = InMemoryMappingRepository()
object_store = InMemoryObjectStore()
asset_repo = InMemoryAssetRepository()
scanner = InMemoryMalwareScanner()

intake_service = IntakeService(asset_repo, object_store, scanner, src_repo, batch_repo)

registry = SourceRegistryService(src_repo, batch_repo)
mapping_service = MappingService(mapping_repo)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sources")
def list_sources():
    items = [asdict(s) for s in src_repo._store.values()]
    return items


@app.post("/sources")
def register_source(payload: dict):
    try:
        src = OnboardingSource(
            id=payload["id"],
            tenant_id=payload["tenant_id"],
            scheme_id=payload["scheme_id"],
            source_name=payload["source_name"],
            source_type=payload["source_type"],
            source_system_product=payload.get("source_system_product", ""),
            source_system_version=payload.get("source_system_version", ""),
            ceding_administrator=payload.get("ceding_administrator"),
            owner_contact=payload.get("owner_contact"),
            delivery_channel=payload.get("delivery_channel"),
            schema_version=payload.get("schema_version"),
            timezone=payload.get("timezone", "UTC"),
            encoding=payload.get("encoding", "utf-8"),
            data_classification=payload.get("data_classification", "internal"),
            expected_extract_type=payload.get("expected_extract_type", "csv"),
            source_authority_profile=payload.get("source_authority_profile"),
            known_defect_profile=payload.get("known_defect_profile"),
            effective_from=_parse_date(payload.get("effective_from")),
            effective_to=_parse_date(payload.get("effective_to")),
        )
        saved = registry.register_source(src)
        return asdict(saved)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/batches")
def create_batch(payload: dict):
    try:
        # minimal required fields
        received_at = datetime.fromisoformat(payload.get("received_at")) if payload.get("received_at") else datetime.now(UTC)
        snapshot = datetime.fromisoformat(payload.get("snapshot_effective_at")) if payload.get("snapshot_effective_at") else datetime.now(UTC)
        batch = OnboardingBatch(
            id=payload["id"],
            tenant_id=payload["tenant_id"],
            scheme_id=payload["scheme_id"],
            source_id=payload["source_id"],
            batch_reference=payload["batch_reference"],
            batch_type=BatchType(payload.get("batch_type", "INITIAL")),
            source_extract_version=payload.get("source_extract_version", "v1"),
            snapshot_effective_at=snapshot,
            received_at=received_at,
            records_received=int(payload.get("records_received", 0)),
        )
        # ensure source exists
        src = src_repo.get_by_id(batch.source_id)
        if src is None:
            raise HTTPException(status_code=404, detail="source not found")
        saved = registry.create_batch(src, batch)
        return asdict(saved)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/batches")
def list_batches(source_id: str | None = Query(None)):
    if source_id:
        return [asdict(b) for b in batch_repo.list_for_source(source_id)]
    return [asdict(b) for b in batch_repo._store.values()]


@app.get("/mapping/packs")
def list_packs(source_type: str | None = Query(None)):
    if not source_type:
        return [asdict(p) for p in mapping_repo._packs.values()]
    packs = mapping_service.list_packs_for_source_type(source_type)
    return [asdict(p) for p in packs]


@app.post("/mapping/suggestions")
def create_suggestion(payload: dict):
    try:
        sug = MappingSuggestion(
            id=payload["id"],
            mapping_pack_id=payload["mapping_pack_id"],
            source_field=payload["source_field"],
            suggested_target_field=payload["suggested_target_field"],
            confidence=float(payload.get("confidence", 0.0)),
            evidence=payload.get("evidence"),
        )
        saved = mapping_service.register_suggestion(sug)
        return asdict(saved)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/assets")
async def upload_asset(payload: dict):
    """Simple JSON-based upload endpoint. Multipart upload belongs in a later storage slice."""
    try:
        content = payload.get("content")
        if content is None:
            raise ValueError("content is required")
        if isinstance(content, str):
            content_bytes = content.encode(payload.get("encoding", "utf-8"))
        else:
            raise ValueError("content must be a string in the current JSON upload contract")

        saved = intake_service.ingest_asset(
            payload["source_id"],
            payload["batch_id"],
            payload.get("filename", "upload.bin"),
            content_bytes,
            payload.get("mime_type", "application/octet-stream"),
            payload.get("retention_policy"),
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return asdict(saved)


@app.get("/assets")
def list_assets(batch_id: str | None = Query(None)):
    if batch_id:
        return [asdict(a) for a in asset_repo.list_for_batch(batch_id)]
    return [asdict(a) for a in asset_repo._store.values()]
