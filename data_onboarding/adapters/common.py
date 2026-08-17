from __future__ import annotations

from collections.abc import Iterable, Iterator


def infer_schema(rows: Iterable[dict]) -> dict:
    values_by_field: dict[str, list[object]] = {}
    for row in rows:
        for field, value in row.items():
            values_by_field.setdefault(field, []).append(value)

    return {
        "fields": [
            {
                "name": field,
                "type": _infer_type(values),
                "nullable": any(value in (None, "") for value in values),
            }
            for field, values in values_by_field.items()
        ]
    }


def read_control_totals(rows: Iterable[dict]) -> dict:
    row_count = 0
    populated_fields: dict[str, int] = {}
    for row in rows:
        row_count += 1
        for field, value in row.items():
            if value not in (None, ""):
                populated_fields[field] = populated_fields.get(field, 0) + 1
    return {"record_count": row_count, "populated_fields": populated_fields}


def filter_delta(rows: Iterable[dict], since_checkpoint: str | None = None, checkpoint_field: str = "updated_at") -> Iterator[dict]:
    for row in rows:
        if since_checkpoint is None:
            yield row
            continue
        checkpoint = row.get(checkpoint_field)
        if checkpoint is not None and str(checkpoint) > since_checkpoint:
            yield row


def _infer_type(values: list[object]) -> str:
    present = [value for value in values if value not in (None, "")]
    if not present:
        return "unknown"
    if all(isinstance(value, bool) for value in present):
        return "boolean"
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in present):
        return "number"
    return "string"
