from __future__ import annotations

import json
from typing import Iterator

from data_onboarding.adapters.common import filter_delta, infer_schema, read_control_totals
from data_onboarding.adapters.ports import AdapterPort


class JSONAdapter(AdapterPort):
    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def inspect(self, source_meta: dict) -> dict:
        return {"format": "json"}

    def read_schema(self, source_stream: bytes) -> dict:
        return infer_schema(self.stream_records(source_stream))

    def stream_records(self, source_stream: bytes) -> Iterator[dict]:
        text = source_stream.decode(self.encoding)
        text = text.strip()
        if text.startswith("["):
            arr = json.loads(text)
            for obj in arr:
                if not isinstance(obj, dict):
                    raise ValueError("json array records must be objects")
                yield obj
            return
        for line in text.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("json line records must be objects")
            yield obj

    def read_control_totals(self, source_stream: bytes) -> dict:
        return read_control_totals(self.stream_records(source_stream))

    def read_delta(self, source_stream: bytes, since_checkpoint: str | None = None) -> Iterator[dict]:
        return filter_delta(self.stream_records(source_stream), since_checkpoint)
