from __future__ import annotations

from datetime import UTC, datetime

from data_onboarding.domain.batch import BatchStatus, BatchType, OnboardingBatch
from data_onboarding.domain.data_state import DataState
from data_onboarding.domain.source import OnboardingSource
from data_onboarding.repositories.in_memory import InMemoryBatchRepository
from data_onboarding.services.profiling import ProfilingService


def make_source() -> OnboardingSource:
    return OnboardingSource(
        id="src-pr04",
        tenant_id="tenant-1",
        scheme_id="scheme-1",
        source_name="PR04 Source",
        source_type="ADMIN",
        source_system_product="AdminX",
        source_system_version="1.0",
    )


def make_batch(source: OnboardingSource) -> OnboardingBatch:
    now = datetime.now(UTC)
    return OnboardingBatch(
        id="batch-pr04",
        tenant_id=source.tenant_id,
        scheme_id=source.scheme_id,
        source_id=source.id,
        batch_reference="pr04-ref",
        batch_type=BatchType.INITIAL,
        source_extract_version="v1",
        snapshot_effective_at=now,
        received_at=now,
        records_received=3,
        status=BatchStatus.RECEIVED,
    )


def test_profile_batch_records_structured_field_statistics_and_lifecycle():
    source = make_source()
    batch = make_batch(source)
    batch_repo = InMemoryBatchRepository()
    batch_repo.save(batch)
    service = ProfilingService(batch_repo)

    result = service.profile_batch(
        batch,
        sample_rows=[
            {"member_id": "M001", "dob": "1980-01-01", "salary": 2000},
            {"member_id": "M002", "dob": "1981-02-02", "salary": 2100},
            {"member_id": "M003", "dob": "", "salary": None},
        ],
    )

    assert result.record_count == 3
    assert batch_repo.get_by_id(batch.id).status == BatchStatus.READY_FOR_MAPPING
    assert result.field_stats["dob"]["observed_type"] == "date"
    assert result.field_stats["dob"]["blank_count"] == 1
    assert result.field_stats["dob"]["observed_patterns"] == ["iso_date"]
    assert result.field_stats["salary"]["observed_type"] == "number"
    assert result.field_stats["salary"]["null_count"] == 1


def test_expected_fields_distinguish_not_provided_from_unknown_and_confirmed_null():
    source = make_source()
    batch = make_batch(source)
    service = ProfilingService(InMemoryBatchRepository())

    profile = service.create_data_profile(
        batch,
        source_id=source.id,
        expected_fields=["member_id", "leaver_date", "spouse_dob", "gmp_amount"],
        confirmed_null_fields={"spouse_dob"},
        sample_rows=[
            {"member_id": "M001", "spouse_dob": None, "gmp_amount": None},
            {"member_id": "M002", "spouse_dob": None, "gmp_amount": None},
        ],
    )

    observations = {item.field_name: item for item in profile.field_observations}

    assert observations["member_id"].data_state == DataState.KNOWN
    assert observations["leaver_date"].data_state == DataState.NOT_PROVIDED
    assert observations["leaver_date"].provided_count == 0
    assert observations["spouse_dob"].data_state == DataState.CONFIRMED_NULL
    assert observations["gmp_amount"].data_state == DataState.UNKNOWN


def test_not_applicable_fields_are_explicit_policy_inputs():
    source = make_source()
    batch = make_batch(source)
    service = ProfilingService(InMemoryBatchRepository())

    profile = service.create_data_profile(
        batch,
        source_id=source.id,
        expected_fields=["opt_out_date"],
        not_applicable_fields={"opt_out_date"},
        sample_rows=[{"member_id": "M001"}, {"member_id": "M002"}],
    )

    opt_out = next(item for item in profile.field_observations if item.field_name == "opt_out_date")
    assert opt_out.data_state == DataState.NOT_APPLICABLE
    assert opt_out.missing_count == 2


def test_observations_validate_counts_and_ratios():
    source = make_source()
    batch = make_batch(source)
    service = ProfilingService(InMemoryBatchRepository())

    profile = service.create_data_profile(
        batch,
        source_id=source.id,
        sample_rows=[
            {"status_code": "ACTIVE"},
            {"status_code": "DEFERRED"},
            {"status_code": ""},
        ],
    )

    status = profile.field_observations[0]
    assert status.data_state == DataState.KNOWN
    assert status.distinct_count == 2
    assert round(status.null_ratio, 2) == 0.33
    assert status.observed_patterns == ["uppercase_code"]
