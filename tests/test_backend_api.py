from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from backend.app.main import create_batch, list_batches, register_source, upload_asset


def test_backend_intake_flow_quarantines_infected_batch():
    source_payload = {
        "id": "api-src-1",
        "tenant_id": "tenant-1",
        "scheme_id": "scheme-1",
        "source_name": "API Payroll",
        "source_type": "PAYROLL",
        "source_system_product": "PayrollX",
        "source_system_version": "1.0",
    }
    source_response = register_source(source_payload)
    assert source_response["id"] == "api-src-1"

    batch_payload = {
        "id": "api-batch-1",
        "tenant_id": "tenant-1",
        "scheme_id": "scheme-1",
        "source_id": "api-src-1",
        "batch_reference": "api-ref-1",
        "batch_type": "INITIAL",
        "source_extract_version": "v1",
    }
    batch_response = create_batch(batch_payload)
    assert batch_response["status"] == "RECEIVED"

    asset_response = asyncio.run(
        upload_asset(
            {
                "source_id": "api-src-1",
                "batch_id": "api-batch-1",
                "filename": "infected.csv",
                "mime_type": "text/csv",
                "content": "MALWARE payload",
            }
        )
    )
    assert asset_response["metadata"]["malware_status"] == "INFECTED"

    batches_response = list_batches(source_id="api-src-1")
    assert batches_response[0]["status"] == "QUARANTINED"


def test_backend_json_upload_rejects_unknown_source():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            upload_asset(
                {
                    "source_id": "missing-source",
                    "batch_id": "missing-batch",
                    "filename": "unknown.csv",
                    "mime_type": "text/csv",
                    "content": "name,age",
                }
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "source does not exist"
