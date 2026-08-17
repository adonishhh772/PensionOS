from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from data_onboarding.domain.exception import (
    DataQualityIssue,
    ExceptionCategory,
    ExceptionCluster,
    ExceptionResolutionStatus,
    ExceptionSeverity,
    OnboardingException,
)


class ExceptionDetectionService:
    def __init__(self) -> None:
        self._issues: dict[str, DataQualityIssue] = {}
        self._exceptions: dict[str, OnboardingException] = {}
        self._clusters: dict[str, ExceptionCluster] = {}

    def detect_nulls(self, batch_id: str, source_id: str, rows: list[dict], threshold: float = 0.1) -> list[OnboardingException]:
        exceptions: list[OnboardingException] = []
        field_nulls: dict[str, int] = defaultdict(int)

        for row in rows:
            for field, value in row.items():
                if value is None or value == "":
                    field_nulls[field] += 1

        total_rows = len(rows)
        for field, null_count in field_nulls.items():
            null_ratio = null_count / total_rows if total_rows > 0 else 0.0
            if null_ratio > threshold:
                severity = ExceptionSeverity.HIGH if null_ratio > 0.5 else ExceptionSeverity.MEDIUM
                exception = OnboardingException(
                    id=f"exc-null-{batch_id}-{field}",
                    batch_id=batch_id,
                    source_id=source_id,
                    category=ExceptionCategory.COMPLETENESS,
                    severity=severity,
                    description=f"Field '{field}' has {null_count} null values ({null_ratio:.1%}) exceeding threshold {threshold:.1%}",
                    affected_records=null_count,
                    affected_fields=[field],
                    detected_at=datetime.now(UTC),
                    metadata={"null_ratio": str(null_ratio), "threshold": str(threshold)},
                )
                exception.validate()
                exceptions.append(exception)
                self._exceptions[exception.id] = exception

        return exceptions

    def detect_schema_mismatches(
        self, batch_id: str, source_id: str, rows: list[dict], expected_schema: dict[str, str] | None = None
    ) -> list[OnboardingException]:
        exceptions: list[OnboardingException] = []
        if not expected_schema:
            return exceptions

        for row_idx, row in enumerate(rows):
            for field, expected_type in expected_schema.items():
                if field not in row:
                    exception = OnboardingException(
                        id=f"exc-schema-{batch_id}-{field}-{row_idx}",
                        batch_id=batch_id,
                        source_id=source_id,
                        category=ExceptionCategory.SCHEMA_MISMATCH,
                        severity=ExceptionSeverity.HIGH,
                        description=f"Row {row_idx}: Expected field '{field}' (type {expected_type}) not found",
                        affected_records=1,
                        affected_fields=[field],
                        detected_at=datetime.now(UTC),
                        metadata={"expected_type": expected_type, "row_index": str(row_idx)},
                    )
                    exception.validate()
                    exceptions.append(exception)
                    self._exceptions[exception.id] = exception
                    break

        return exceptions

    def detect_duplicates(self, batch_id: str, source_id: str, rows: list[dict], key_fields: list[str]) -> list[OnboardingException]:
        exceptions: list[OnboardingException] = []
        seen: dict[tuple, int] = {}

        for row_idx, row in enumerate(rows):
            key = tuple(row.get(field) for field in key_fields)
            if key in seen:
                exception = OnboardingException(
                    id=f"exc-dup-{batch_id}-{row_idx}",
                    batch_id=batch_id,
                    source_id=source_id,
                    category=ExceptionCategory.DUPLICATE,
                    severity=ExceptionSeverity.MEDIUM,
                    description=f"Duplicate record detected (key={key}). First occurrence at row {seen[key]}, duplicate at row {row_idx}",
                    affected_records=2,
                    affected_fields=key_fields,
                    detected_at=datetime.now(UTC),
                    metadata={"first_row": str(seen[key]), "duplicate_row": str(row_idx), "key": str(key)},
                )
                exception.validate()
                exceptions.append(exception)
                self._exceptions[exception.id] = exception
            else:
                seen[key] = row_idx

        return exceptions

    def cluster_exceptions(self, batch_id: str, exceptions: list[OnboardingException]) -> list[ExceptionCluster]:
        clusters: list[ExceptionCluster] = []
        clustered_ids = set()

        by_category = defaultdict(list)
        for exc in exceptions:
            by_category[exc.category].append(exc)

        for category, excs in by_category.items():
            if len(excs) >= 2:
                cluster = ExceptionCluster(
                    id=f"cluster-{batch_id}-{category.value}",
                    batch_id=batch_id,
                    root_cause=f"Multiple {category.value} issues detected",
                    category=category,
                    severity=max(exc.severity for exc in excs),
                    member_exceptions=[exc.id for exc in excs],
                    affected_record_count=sum(exc.affected_records for exc in excs),
                    created_at=datetime.now(UTC),
                )
                cluster.validate()
                clusters.append(cluster)
                self._clusters[cluster.id] = cluster
                for exc in excs:
                    clustered_ids.add(exc.id)

        return clusters

    def get_exception(self, exception_id: str) -> OnboardingException | None:
        return self._exceptions.get(exception_id)

    def get_cluster(self, cluster_id: str) -> ExceptionCluster | None:
        return self._clusters.get(cluster_id)

    def list_exceptions_for_batch(self, batch_id: str) -> list[OnboardingException]:
        return [e for e in self._exceptions.values() if e.batch_id == batch_id]

    def list_clusters_for_batch(self, batch_id: str) -> list[ExceptionCluster]:
        return [c for c in self._clusters.values() if c.batch_id == batch_id]

    def mark_exception_resolved(self, exception_id: str, resolution_notes: str | None = None) -> OnboardingException | None:
        exc = self._exceptions.get(exception_id)
        if exc:
            exc.resolution_status = ExceptionResolutionStatus.RESOLVED
            exc.resolution_notes = resolution_notes
            exc.resolved_at = datetime.now(UTC)
        return exc

    def mark_cluster_resolved(self, cluster_id: str, resolution_notes: str | None = None) -> ExceptionCluster | None:
        cluster = self._clusters.get(cluster_id)
        if cluster:
            cluster.resolution_status = ExceptionResolutionStatus.RESOLVED
            cluster.resolved_at = datetime.now(UTC)
        return cluster
