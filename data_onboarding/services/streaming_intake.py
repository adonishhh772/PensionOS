from __future__ import annotations

from data_onboarding.adapters.ports import AdapterPort


class StreamingIntakeService:
    def __init__(self, adapter: AdapterPort) -> None:
        self.adapter = adapter

    def stream_rows(self, source_stream: bytes) -> list[dict]:
        rows = list(self.adapter.stream_records(source_stream))
        return rows

    def chunk_rows(self, source_stream: bytes, chunk_size: int = 1000) -> list[list[dict]]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        rows = list(self.adapter.stream_records(source_stream))
        return [rows[i:i + chunk_size] for i in range(0, len(rows), chunk_size)]

    def inspect(self, source_meta: dict) -> dict:
        return self.adapter.inspect(source_meta)

    def read_schema(self, source_stream: bytes) -> dict:
        return self.adapter.read_schema(source_stream)

    def read_control_totals(self, source_stream: bytes) -> dict:
        return self.adapter.read_control_totals(source_stream)

    def read_delta(self, source_stream: bytes, since_checkpoint: str | None = None) -> list[dict]:
        return list(self.adapter.read_delta(source_stream, since_checkpoint))
