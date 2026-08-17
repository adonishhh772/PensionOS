from __future__ import annotations

from datetime import UTC, datetime

from data_onboarding.domain.source import OnboardingSource
from data_onboarding.domain.batch import OnboardingBatch, BatchType, BatchStatus
from data_onboarding.domain.mapping import (
    MappingPack,
    MappingSuggestion,
    FieldMappingRule,
    MappingApprovalPolicy,
    MappingApprovalStatus,
)
from data_onboarding.domain.data_state import DataState
from data_onboarding.repositories.in_memory import (
    InMemorySourceRepository,
    InMemoryBatchRepository,
    InMemoryMappingRepository,
)
from data_onboarding.services.profiling import ProfilingService
from data_onboarding.services.mapping_pack import MappingService


def make_source() -> OnboardingSource:
    return OnboardingSource(
        id="src-2",
        tenant_id="t1",
        scheme_id="sch-1",
        source_name="PayrollSys2",
        source_type="payroll",
        source_system_product="PaySoft",
        source_system_version="1.2.3",
    )


def make_batch(source: OnboardingSource) -> OnboardingBatch:
    now = datetime.now(UTC)
    return OnboardingBatch(
        id="batch-2",
        tenant_id=source.tenant_id,
        scheme_id=source.scheme_id,
        source_id=source.id,
        batch_reference="ref-2",
        batch_type=BatchType.INITIAL,
        source_extract_version="v1",
        snapshot_effective_at=now,
        received_at=now,
        records_received=100,
    )


def test_profiling_and_mapping_flow():
    src_repo = InMemorySourceRepository()
    batch_repo = InMemoryBatchRepository()
    map_repo = InMemoryMappingRepository()

    src = make_source()
    src_repo.save(src)
    batch = make_batch(src)
    batch_repo.save(batch)

    profiler = ProfilingService(batch_repo)
    result = profiler.profile_batch(batch)
    assert result.record_count == 100
    # batch should be READY_FOR_MAPPING
    b = batch_repo.get_by_id(batch.id)
    assert b is not None and b.status == BatchStatus.READY_FOR_MAPPING

    mapping_service = MappingService(map_repo)
    pack = MappingPack(id="pack-1", source_type=src.source_type, version="v1")
    saved_pack = mapping_service.create_pack(pack)
    assert saved_pack.id == pack.id

    suggestion = MappingSuggestion(
        id="sug-1",
        mapping_pack_id=pack.id,
        source_field="dob",
        suggested_target_field="person.date_of_birth",
        confidence=0.85,
    )

    saved_sug = mapping_service.register_suggestion(suggestion)
    assert saved_sug.id == suggestion.id
    suggestions = mapping_service.list_suggestions(pack.id)
    assert any(s.id == suggestion.id for s in suggestions)


def test_data_state_profile_semantics():
    batch_repo = InMemoryBatchRepository()
    profiler = ProfilingService(batch_repo)
    source = make_source()
    batch = make_batch(source)
    profile = profiler.create_data_profile(
        batch,
        source_id=source.id,
        sample_rows=[
            {"dob": "1980-01-01", "gross_pay": 2000},
            {"dob": None, "gross_pay": 2100},
            {"dob": "1982-02-02", "gross_pay": None},
        ],
    )

    assert profile.total_records == 3
    dob_obs = next(item for item in profile.field_observations if item.field_name == "dob")
    assert dob_obs.data_state == DataState.KNOWN
    assert dob_obs.null_count == 1
    gross_obs = next(item for item in profile.field_observations if item.field_name == "gross_pay")
    assert gross_obs.data_state == DataState.KNOWN
    assert gross_obs.null_count == 1


def test_data_state_enum_has_required_values():
    values = set(DataState.values())
    required = {
        "KNOWN",
        "UNKNOWN",
        "NOT_PROVIDED",
        "NOT_APPLICABLE",
        "CONFLICTING",
        "DERIVED",
        "CONFIRMED_NULL",
        "PENDING_REVIEW",
    }
    assert required.issubset(values)


def test_mapping_pack_engine_and_approvals():
    map_repo = InMemoryMappingRepository()
    service = MappingService(map_repo)

    pack = MappingPack(id="pack-approval", source_type="payroll", version="v2")
    service.create_pack(pack)
    service.add_field_mapping(pack.id, "salary", "member.gross_salary")
    rule = FieldMappingRule(
        source_field="salary",
        target_field="member.gross_salary",
        source_type="payroll",
        target_domain="member",
        materiality="high",
    )
    service.add_field_rule(pack.id, rule)

    policy = MappingApprovalPolicy(
        id="policy-1",
        source_type="payroll",
        field_domain="member.salary",
        requires_human_approval=True,
        min_confidence=0.8,
        required_tests=["unit", "reconciliation"],
        human_roles=["validator"],
        materiality="high",
    )
    assert service.evaluate_policy(policy, confidence=0.7, material=True) is True

    approval = service.request_approval(pack.id, "salary", "member.gross_salary", rationale="material salary mapping")
    assert approval.status == MappingApprovalStatus.PENDING

    approved = service.approve_mapping(approval.id, approved_by="validator", rationale="approved by policy", approved=True)
    assert approved.status == MappingApprovalStatus.APPROVED
    approvals = service.list_approvals(pack.id)
    assert any(a.id == approval.id for a in approvals)


def test_mapping_pack_target_lookup():
    pack = MappingPack(id="pack-map", source_type="payroll", version="v1")
    pack.add_mapping("dob", "person.date_of_birth")
    assert pack.target_for("dob") == "person.date_of_birth"
    assert pack.target_for("missing") is None
