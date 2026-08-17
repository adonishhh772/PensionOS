from __future__ import annotations

from typing import Iterator, List

from data_onboarding.adapters.common import filter_delta, infer_schema, read_control_totals
from data_onboarding.adapters.ports import AdapterPort


class FixedWidthAdapter(AdapterPort):
    def __init__(self, column_widths: List[int], encoding: str = "utf-8") -> None:
        self.column_widths = column_widths
        self.encoding = encoding

    def inspect(self, source_meta: dict) -> dict:
        return {"format": "fixed-width", "widths": self.column_widths}

    def read_schema(self, source_stream: bytes) -> dict:
        return infer_schema(self.stream_records(source_stream))

    def stream_records(self, source_stream: bytes) -> Iterator[dict]:
        text = source_stream.decode(self.encoding)
        for line in text.splitlines():
            if not line.strip():
                continue
            pos = 0
            values: list[str] = []
            for width in self.column_widths:
                values.append(line[pos:pos + width].strip())
                pos += width
            yield {f"col_{i}": values[i] for i in range(len(values))}

    def read_control_totals(self, source_stream: bytes) -> dict:
        return read_control_totals(self.stream_records(source_stream))

    def read_delta(self, source_stream: bytes, since_checkpoint: str | None = None) -> Iterator[dict]:
        return filter_delta(self.stream_records(source_stream), since_checkpoint)
