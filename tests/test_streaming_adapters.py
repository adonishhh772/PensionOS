from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from data_onboarding.adapters.csv_adapter import CSVAdapter
from data_onboarding.adapters.fixed_width_adapter import FixedWidthAdapter
from data_onboarding.adapters.json_adapter import JSONAdapter
from data_onboarding.adapters.xlsx_adapter import XLSXAdapter
from data_onboarding.services.streaming_intake import StreamingIntakeService


def test_csv_streaming():
    adapter = CSVAdapter()
    payload = b"name,age\nAlice,30\nBob,40\n"
    rows = list(adapter.stream_records(payload))
    assert rows == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "40"}]


def test_json_streaming():
    adapter = JSONAdapter()
    payload = b'{"name":"Alice","age":30}\n{"name":"Bob","age":40}\n'
    rows = list(adapter.stream_records(payload))
    assert rows == [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 40}]


def test_fixed_width_streaming():
    adapter = FixedWidthAdapter([5, 3])
    payload = b"Alice30\nBob  40\n"
    rows = list(adapter.stream_records(payload))
    assert rows[0]["col_0"] == "Alice"
    assert rows[0]["col_1"] == "30"


def test_streaming_intake_service_chunks():
    adapter = CSVAdapter()
    service = StreamingIntakeService(adapter)
    payload = b"name,age\nAlice,30\nBob,40\nCarol,50\n"
    rows = service.stream_rows(payload)
    chunks = service.chunk_rows(payload, chunk_size=2)
    assert len(rows) == 3
    assert len(chunks) == 2


def test_csv_schema_control_totals_and_delta():
    adapter = CSVAdapter()
    payload = (
        b"id,name,updated_at\n"
        b"1,Alice,2026-01-01T10:00:00\n"
        b"2,Bob,2026-01-03T10:00:00\n"
    )

    schema = adapter.read_schema(payload)
    assert [field["name"] for field in schema["fields"]] == ["id", "name", "updated_at"]

    totals = adapter.read_control_totals(payload)
    assert totals["record_count"] == 2
    assert totals["populated_fields"]["name"] == 2

    delta_rows = list(adapter.read_delta(payload, since_checkpoint="2026-01-02T00:00:00"))
    assert delta_rows == [{"id": "2", "name": "Bob", "updated_at": "2026-01-03T10:00:00"}]


def test_json_schema_infers_native_types():
    adapter = JSONAdapter()
    payload = b'[{"id":1,"active":true,"score":10.5},{"id":2,"active":false,"score":null}]'

    schema = adapter.read_schema(payload)
    field_types = {field["name"]: field["type"] for field in schema["fields"]}
    assert field_types == {"id": "number", "active": "boolean", "score": "number"}


def test_json_rejects_non_object_records():
    adapter = JSONAdapter()

    with pytest.raises(ValueError, match="records must be objects"):
        list(adapter.stream_records(b'["not-an-object"]'))


def test_fixed_width_control_totals():
    adapter = FixedWidthAdapter([5, 3])
    payload = b"Alice30\nBob  40\n"

    totals = adapter.read_control_totals(payload)
    assert totals["record_count"] == 2
    assert totals["populated_fields"] == {"col_0": 2, "col_1": 2}


def test_xlsx_streaming_schema_and_control_totals():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["id", "name", "updated_at"])
    sheet.append([1, "Alice", "2026-01-01T10:00:00"])
    sheet.append([2, "Bob", "2026-01-03T10:00:00"])

    output = io.BytesIO()
    workbook.save(output)
    payload = output.getvalue()

    adapter = XLSXAdapter()
    rows = list(adapter.stream_records(payload))
    assert rows[0]["name"] == "Alice"

    totals = adapter.read_control_totals(payload)
    assert totals["record_count"] == 2

    delta_rows = list(adapter.read_delta(payload, since_checkpoint="2026-01-02T00:00:00"))
    assert len(delta_rows) == 1
    assert delta_rows[0]["name"] == "Bob"


def test_streaming_intake_service_exposes_adapter_contract_and_validates_chunk_size():
    service = StreamingIntakeService(CSVAdapter())
    payload = b"id,updated_at\n1,2026-01-01T10:00:00\n2,2026-01-03T10:00:00\n"

    assert service.inspect({})["format"] == "csv"
    assert service.read_control_totals(payload)["record_count"] == 2
    assert len(service.read_schema(payload)["fields"]) == 2
    assert service.read_delta(payload, since_checkpoint="2026-01-02T00:00:00")[0]["id"] == "2"

    with pytest.raises(ValueError, match="chunk_size"):
        service.chunk_rows(payload, chunk_size=0)
