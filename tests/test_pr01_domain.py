from datetime import datetime

import pytest

from data_onboarding.domain.authority import AuthorityClass, SourceAuthorityPolicy
from data_onboarding.domain.batch import BatchStatus, BatchType, OnboardingBatch
from data_onboarding.domain.source import OnboardingSource, SourceStatus
from data_onboarding.services.source_registry import SourceRegistryService


class InMemorySourceRepo:
    def __init__(self):
        self.items = {}

    def save(self, source):
        self.items[source.id] = source
        return source

    def get_by_id(self, source_id):
        return self.items.get(source_id)

    def list_for_scheme(self, scheme_id):
        return [item for item in self.items.values() if item.scheme_id == scheme_id]


class InMemoryBatchRepo:
    def __init__(self):
        self.items = {}

    def save(self, batch):
        self.items[batch.id] = batch
        return batch

    def get_by_id(self, batch_id):
        return self.items.get(batch_id)

    def list_for_source(self, source_id):
        return [item for item in self.items.values() if item.source_id == source_id]


def make_source(source_id="src-001", scheme_id="scheme-001"):
    return OnboardingSource(
        id=source_id,
        tenant_id="tenant-001",
        scheme_id=scheme_id,
        source_name="Employer Payroll Export",
        source_type="PAYROLL",
        source_system_product="PayrollX",
        source_system_version="2.4",
        delivery_channel="sftp",
        expected_extract_type="csv",
        status=SourceStatus.ACTIVE,
    )


def make_batch(source_id="src-001", scheme_id="scheme-001", batch_id="batch-001"):
    return OnboardingBatch(
        id=batch_id,
        tenant_id="tenant-001",
        scheme_id=scheme_id,
        source_id=source_id,
        batch_reference="Q3-2026-01",
        batch_type=BatchType.INITIAL,
        source_extract_version="v1",
        snapshot_effective_at=datetime(2026, 7, 1, 9, 0, 0),
        received_at=datetime(2026, 7, 2, 12, 0, 0),
        source_control_totals={"records": 1500},
        records_received=1500,
        records_processed=0,
        processing_statistics={"rows_seen": 0},
        policy_snapshot_id="policy-001",
        status=BatchStatus.RECEIVED,
    )


def test_source_registration_requires_required_fields():
    with pytest.raises(ValueError, match="scheme_id is required"):
        OnboardingSource(
            id="src-002",
            tenant_id="tenant-001",
            scheme_id="",
            source_name="Missing Scheme",
            source_type="PAYROLL",
            source_system_product="PayrollX",
            source_system_version="2.4",
        ).validate()


def test_source_registry_rejects_duplicate_name_in_same_scheme():
    source_repo = InMemorySourceRepo()
    batch_repo = InMemoryBatchRepo()
    service = SourceRegistryService(source_repo, batch_repo)
    source = make_source()
    service.register_source(source)

    duplicate = make_source(source_id="src-002")
    with pytest.raises(ValueError, match="same name and type"):
        service.register_source(duplicate)


def test_batch_lifecycle_allows_valid_transition():
    batch = make_batch()
    batch.transition_to(BatchStatus.VALIDATING)
    assert batch.status == BatchStatus.VALIDATING


def test_batch_lifecycle_rejects_invalid_transition():
    batch = make_batch()
    with pytest.raises(ValueError, match="invalid batch lifecycle transition"):
        batch.transition_to(BatchStatus.COMPLETED)


def test_batch_partial_processing_only_valid_when_processing():
    batch = make_batch()
    batch.status = BatchStatus.PROCESSING
    batch.mark_partial_processing()
    assert batch.status == BatchStatus.PARTIALLY_PROCESSED

    other = make_batch(batch_id="batch-002")
    with pytest.raises(ValueError, match="partial processing"):
        other.mark_partial_processing()


def test_service_creates_batch_only_for_matching_source_and_scheme():
    source_repo = InMemorySourceRepo()
    batch_repo = InMemoryBatchRepo()
    service = SourceRegistryService(source_repo, batch_repo)
    source = make_source()
    service.register_source(source)

    batch = make_batch()
    created = service.create_batch(source, batch)
    assert created.status == BatchStatus.RECEIVED

    wrong_source = make_source(source_id="src-777", scheme_id="scheme-999")
    bad_batch = make_batch(source_id="src-999", scheme_id="scheme-001", batch_id="bad-batch")
    with pytest.raises(ValueError, match="must match the source id"):
        service.create_batch(wrong_source, bad_batch)


def test_authority_policy_validation_ensures_consistent_dates():
    policy = SourceAuthorityPolicy(
        id="auth-1",
        version="v1",
        field_domain_group="DOB",
        source_type="PAYROLL",
        authority_class=AuthorityClass.PRIMARY,
        effective_from=None,
        effective_to=None,
    )
    assert policy.validate() is None

    invalid = SourceAuthorityPolicy(
        id="auth-2",
        version="v1",
        field_domain_group="GMP",
        source_type="ADMIN_MASTER",
        authority_class=AuthorityClass.SUPPORTING,
        effective_from=None,
        effective_to=None,
    )
    invalid.effective_from = None
    invalid.effective_to = None
    assert invalid.validate() is None
