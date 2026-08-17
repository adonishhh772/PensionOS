from __future__ import annotations

from typing import Iterator, Protocol


class AdapterPort(Protocol):
    def inspect(self, source_meta: dict) -> dict:
        ...

    def read_schema(self, source_stream: bytes) -> dict:
        ...

    def stream_records(self, source_stream: bytes) -> Iterator[dict]:
        """Yield records as dicts from a bytes stream."""
        ...

    def read_control_totals(self, source_stream: bytes) -> dict:
        ...

    def read_delta(self, source_stream: bytes, since_checkpoint: str | None = None) -> Iterator[dict]:
        ...
