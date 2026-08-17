from __future__ import annotations

from data_onboarding.domain.batch import BatchStatus, OnboardingBatch
from data_onboarding.domain.source import OnboardingSource
from data_onboarding.repositories.ports import BatchRepositoryPort, SourceRepositoryPort


class SourceRegistryService:
    def __init__(self, source_repo: SourceRepositoryPort, batch_repo: BatchRepositoryPort):
        self.source_repo = source_repo
        self.batch_repo = batch_repo

    def register_source(self, source: OnboardingSource) -> OnboardingSource:
        source.validate()
        existing = self.source_repo.list_for_scheme(source.scheme_id)
        if any(item.source_name.lower() == source.source_name.lower() and item.source_type == source.source_type for item in existing):
            raise ValueError("a source with the same name and type already exists for this scheme")
        return self.source_repo.save(source)

    def create_batch(self, source: OnboardingSource, batch: OnboardingBatch) -> OnboardingBatch:
        source.validate()
        batch.validate()
        if source.id != batch.source_id:
            raise ValueError("batch source_id must match the source id")
        if source.scheme_id != batch.scheme_id:
            raise ValueError("batch scheme_id must match the source scheme_id")
        if batch.status != BatchStatus.RECEIVED:
            raise ValueError("new batch must begin in RECEIVED status")
        return self.batch_repo.save(batch)

    def transition_batch(self, batch: OnboardingBatch, target_status: BatchStatus) -> OnboardingBatch:
        batch.transition_to(target_status)
        return self.batch_repo.save(batch)
