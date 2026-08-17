from __future__ import annotations

from datetime import UTC, datetime

from data_onboarding.domain.source import OnboardingSource
from data_onboarding.domain.batch import OnboardingBatch, BatchType, BatchStatus
from data_onboarding.domain.authority import SourceAuthorityPolicy, AuthorityClass
from data_onboarding.repositories.in_memory import (
    InMemorySourceRepository,
    InMemoryBatchRepository,
    InMemoryPolicyRepository,
)
from data_onboarding.services.source_registry import SourceRegistryService
from data_onboarding.services.source_authority import SourceAuthorityService


def make_source() -> OnboardingSource:
    return OnboardingSource(
        id="src-1",
        tenant_id="t1",
        scheme_id="sch-1",
        source_name="PayrollSys",
        source_type="payroll",
        source_system_product="PaySoft",
        source_system_version="1.2.3",
    )


def make_batch(source: OnboardingSource) -> OnboardingBatch:
    now = datetime.now(UTC)
    return OnboardingBatch(
        id="batch-1",
        tenant_id=source.tenant_id,
        scheme_id=source.scheme_id,
        source_id=source.id,
        batch_reference="ref-1",
        batch_type=BatchType.INITIAL,
        source_extract_version="v1",
        snapshot_effective_at=now,
        received_at=now,
    )


def test_source_registry_and_policy_integration():
    src_repo = InMemorySourceRepository()
    batch_repo = InMemoryBatchRepository()
    policy_repo = InMemoryPolicyRepository()

    registry = SourceRegistryService(src_repo, batch_repo)
    authority = SourceAuthorityService(policy_repo)

    s = make_source()
    saved = registry.register_source(s)
    assert saved.id == s.id

    b = make_batch(s)
    saved_batch = registry.create_batch(s, b)
    assert saved_batch.id == b.id
    assert saved_batch.status == BatchStatus.RECEIVED

    policy = SourceAuthorityPolicy(
        id="pol-1",
        version="1",
        field_domain_group="personal/dob",
        source_type=s.source_type,
        authority_class=AuthorityClass.PRIMARY,
    )

    reg_pol = authority.register_policy(policy)
    assert reg_pol.id == policy.id
    listed = authority.list_policies_for_source_type(s.source_type)
    assert any(p.id == policy.id for p in listed)
