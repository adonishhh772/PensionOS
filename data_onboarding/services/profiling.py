from __future__ import annotations

from datetime import UTC, datetime
import re

from data_onboarding.domain.batch import OnboardingBatch, BatchStatus
from data_onboarding.domain.data_state import DataState
from data_onboarding.domain.profiling import ProfilingResult, ProfileObservation, DataProfile
from data_onboarding.repositories.ports import BatchRepositoryPort


class ProfilingService:
    def __init__(self, batch_repo: BatchRepositoryPort) -> None:
        self.batch_repo = batch_repo

    @staticmethod
    def _summarise_field(
        rows: list[dict],
        field_name: str,
        confirmed_null_fields: set[str] | None = None,
        not_applicable_fields: set[str] | None = None,
    ) -> ProfileObservation:
        confirmed_null_fields = confirmed_null_fields or set()
        not_applicable_fields = not_applicable_fields or set()
        total_count = len(rows)
        provided_count = 0
        missing_count = 0
        null_count = 0
        blank_count = 0
        present_values: list[object] = []
        sample_values: list[str] = []
        for row in rows:
            if field_name not in row:
                missing_count += 1
                continue
            provided_count += 1
            value = row[field_name]
            if value is None:
                null_count += 1
                continue
            if value == "":
                blank_count += 1
                continue
            present_values.append(value)
            sample_values.append(str(value))

        observed_type = "unknown"
        if present_values and all(isinstance(value, bool) for value in present_values):
            observed_type = "boolean"
        elif present_values and all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in present_values):
            observed_type = "number"
        elif present_values and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)) for value in present_values):
            observed_type = "date"
        elif present_values:
            observed_type = "string"

        if field_name in not_applicable_fields:
            state = DataState.NOT_APPLICABLE
        elif field_name in confirmed_null_fields:
            state = DataState.CONFIRMED_NULL
        elif provided_count == 0:
            state = DataState.NOT_PROVIDED
        elif present_values:
            state = DataState.KNOWN
        elif blank_count > 0 and null_count == 0:
            state = DataState.NOT_PROVIDED
        else:
            state = DataState.UNKNOWN

        observation = ProfileObservation(
            id=f"obs-{field_name}",
            field_name=field_name,
            observed_type=observed_type,
            data_state=state,
            total_count=total_count,
            provided_count=provided_count,
            missing_count=missing_count,
            null_count=null_count,
            blank_count=blank_count,
            distinct_count=len({str(value) for value in present_values}),
            null_ratio=(null_count + blank_count + missing_count) / total_count if total_count else 0.0,
            sample_values=sample_values[:3],
            observed_patterns=ProfilingService._observed_patterns(present_values),
            notes="derived from sample row population",
        )
        observation.validate()
        return observation

    @staticmethod
    def _observed_patterns(values: list[object]) -> list[str]:
        string_values = [str(value) for value in values]
        patterns: list[str] = []
        if string_values and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) for value in string_values):
            patterns.append("iso_date")
        if string_values and all(value.isdigit() for value in string_values):
            patterns.append("numeric_string")
        if string_values and all(re.fullmatch(r"[A-Z0-9_ -]+", value) and re.search(r"[A-Z]", value) for value in string_values):
            patterns.append("uppercase_code")
        return patterns

    def profile_batch(
        self,
        batch: OnboardingBatch,
        sample_rows: list[dict] | None = None,
        expected_fields: list[str] | None = None,
        confirmed_null_fields: set[str] | None = None,
        not_applicable_fields: set[str] | None = None,
    ) -> ProfilingResult:
        if batch.status not in {BatchStatus.RECEIVED, BatchStatus.READY_FOR_PROFILING}:
            raise ValueError("batch must be RECEIVED or READY_FOR_PROFILING to profile")

        if batch.status == BatchStatus.RECEIVED:
            batch.transition_to(BatchStatus.READY_FOR_PROFILING)
            self.batch_repo.save(batch)

        batch.transition_to(BatchStatus.PROFILING)
        self.batch_repo.save(batch)

        rows = sample_rows or []
        field_names = sorted(set(expected_fields or []) | {key for row in rows for key in row.keys()})
        observations = [
            self._summarise_field(rows, field_name, confirmed_null_fields, not_applicable_fields)
            for field_name in field_names
        ]

        result = ProfilingResult(
            id=f"prof-{batch.id}",
            batch_id=batch.id,
            record_count=len(rows) if rows else batch.records_received,
            field_stats={
                field_name: {
                    "null_count": item.null_count,
                    "blank_count": item.blank_count,
                    "missing_count": item.missing_count,
                    "provided_count": item.provided_count,
                    "distinct_count": item.distinct_count,
                    "null_ratio": item.null_ratio,
                    "observed_type": item.observed_type,
                    "data_state": item.data_state.value,
                    "observed_patterns": item.observed_patterns,
                }
                for field_name, item in zip(field_names, observations)
            },
            profile_observations=observations,
            created_at=datetime.now(UTC),
        )
        result.validate()

        batch.transition_to(BatchStatus.READY_FOR_MAPPING)
        self.batch_repo.save(batch)
        return result

    def create_data_profile(
        self,
        batch: OnboardingBatch,
        source_id: str,
        sample_rows: list[dict] | None = None,
        expected_fields: list[str] | None = None,
        confirmed_null_fields: set[str] | None = None,
        not_applicable_fields: set[str] | None = None,
    ) -> DataProfile:
        rows = sample_rows or []
        field_names = sorted(set(expected_fields or []) | {key for row in rows for key in row.keys()})
        observations = [
            self._summarise_field(rows, field_name, confirmed_null_fields, not_applicable_fields)
            for field_name in field_names
        ]
        profile = DataProfile(
            id=f"profile-{batch.id}",
            batch_id=batch.id,
            source_id=source_id,
            total_records=len(rows),
            field_observations=observations,
            generated_at=datetime.now(UTC),
        )
        profile.validate()
        return profile
