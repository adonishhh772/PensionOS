from __future__ import annotations

import csv
import io
from typing import Iterator

from data_onboarding.adapters.common import filter_delta, infer_schema, read_control_totals
from data_onboarding.adapters.ports import AdapterPort


class CSVAdapter(AdapterPort):
    def __init__(self, encoding: str = "utf-8", delimiter: str = ",") -> None:
        self.encoding = encoding
        self.delimiter = delimiter

    def inspect(self, source_meta: dict) -> dict:
        return {"format": "csv", "delimiter": source_meta.get("delimiter", self.delimiter)}

    def read_schema(self, source_stream: bytes) -> dict:
        return infer_schema(self.stream_records(source_stream))

    def stream_records(self, source_stream: bytes) -> Iterator[dict]:
        text = source_stream.decode(self.encoding)
        reader = csv.DictReader(io.StringIO(text), delimiter=self.delimiter)
        for row in reader:
            yield dict(row)

    def read_control_totals(self, source_stream: bytes) -> dict:
        return read_control_totals(self.stream_records(source_stream))

    def read_delta(self, source_stream: bytes, since_checkpoint: str | None = None) -> Iterator[dict]:
        return filter_delta(self.stream_records(source_stream), since_checkpoint)
