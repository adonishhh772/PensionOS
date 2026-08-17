from __future__ import annotations

from data_onboarding.domain.authority import SourceAuthorityPolicy
from data_onboarding.repositories.ports import PolicyRepositoryPort


class SourceAuthorityService:
    def __init__(self, policy_repo: PolicyRepositoryPort) -> None:
        self.policy_repo = policy_repo

    def register_policy(self, policy: SourceAuthorityPolicy) -> SourceAuthorityPolicy:
        policy.validate()
        existing = self.policy_repo.get_by_id(policy.id)
        if existing is not None:
            raise ValueError("policy with same id already exists")
        return self.policy_repo.save(policy)

    def list_policies_for_source_type(self, source_type: str) -> list[SourceAuthorityPolicy]:
        return self.policy_repo.list_for_source_type(source_type)
