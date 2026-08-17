from __future__ import annotations

from datetime import UTC, datetime

from data_onboarding.domain.mapping import (
    CodeTranslationRule,
    DerivationRule,
    FieldMappingRule,
    MappingApproval,
    MappingApprovalPolicy,
    MappingApprovalStatus,
    MappingPackStatus,
    MappingPack,
    MappingSuggestion,
    MappingTestCase,
    RelationshipMappingRule,
)
from data_onboarding.repositories.ports import MappingRepositoryPort


class MappingService:
    def __init__(self, mapping_repo: MappingRepositoryPort) -> None:
        self.mapping_repo = mapping_repo

    def create_pack(self, pack: MappingPack) -> MappingPack:
        pack.validate()
        existing = self.mapping_repo.get_pack(pack.id)
        if existing is not None:
            raise ValueError("mapping pack with id already exists")
        pack.created_at = datetime.now(UTC)
        return self.mapping_repo.save_pack(pack)

    def add_field_mapping(self, pack_id: str, source_field: str, target_field: str) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        self._ensure_editable(pack)
        pack.add_mapping(source_field, target_field)
        return self.mapping_repo.save_pack(pack)

    def add_field_rule(self, pack_id: str, rule: FieldMappingRule) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        self._ensure_editable(pack)
        rule.validate()
        pack._validate_target_field(rule.target_field)
        pack.field_rules.append(rule)
        return self.mapping_repo.save_pack(pack)

    def add_code_rule(self, pack_id: str, rule: CodeTranslationRule) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        self._ensure_editable(pack)
        rule.validate()
        pack._validate_target_field(rule.target_field)
        pack.code_rules.append(rule)
        return self.mapping_repo.save_pack(pack)

    def add_relationship_rule(self, pack_id: str, rule: RelationshipMappingRule) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        self._ensure_editable(pack)
        rule.validate()
        pack.relationship_rules.append(rule)
        return self.mapping_repo.save_pack(pack)

    def add_derivation_rule(self, pack_id: str, rule: DerivationRule) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        self._ensure_editable(pack)
        rule.validate()
        pack._validate_target_field(rule.target_field)
        pack.derivation_rules.append(rule)
        return self.mapping_repo.save_pack(pack)

    def add_test_case(self, pack_id: str, test_case: MappingTestCase) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        self._ensure_editable(pack)
        test_case.validate()
        pack.test_cases.append(test_case)
        return self.mapping_repo.save_pack(pack)

    def activate_pack(self, pack_id: str) -> MappingPack:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        pack.activate()
        return self.mapping_repo.save_pack(pack)

    def supersede_pack(self, old_pack_id: str, replacement_pack_id: str) -> MappingPack:
        old_pack = self.mapping_repo.get_pack(old_pack_id)
        if old_pack is None:
            raise ValueError("mapping pack not found")
        if self.mapping_repo.get_pack(replacement_pack_id) is None:
            raise ValueError("replacement mapping pack not found")
        old_pack.supersede(replacement_pack_id)
        return self.mapping_repo.save_pack(old_pack)

    def resolve_target(self, packs: list[MappingPack], source_field: str) -> str | None:
        for pack in sorted(packs, key=self._overlay_priority, reverse=True):
            if pack.status != MappingPackStatus.ACTIVE:
                continue
            target = pack.target_for(source_field)
            if target is not None:
                return target
        return None

    def translate_code(self, pack_id: str, source_field: str, target_field: str, source_code: str) -> str | None:
        pack = self.mapping_repo.get_pack(pack_id)
        if pack is None:
            raise ValueError("mapping pack not found")
        if pack.status != MappingPackStatus.ACTIVE:
            raise ValueError("mapping pack must be ACTIVE")
        for rule in pack.code_rules:
            if rule.source_field == source_field and rule.target_field == target_field and rule.source_code == source_code:
                return rule.target_code
        return None

    def register_suggestion(self, suggestion: MappingSuggestion) -> MappingSuggestion:
        suggestion.validate()
        suggestion.created_at = datetime.now(UTC)
        return self.mapping_repo.save_suggestion(suggestion)

    def evaluate_policy(self, policy: MappingApprovalPolicy, confidence: float | None = None, material: bool = False) -> bool:
        policy.validate()
        return policy.requires_review(confidence=confidence, material=material)

    def request_approval(self, mapping_pack_id: str, source_field: str, target_field: str, rationale: str | None = None) -> MappingApproval:
        approval = MappingApproval(
            id=f"approval-{mapping_pack_id}-{source_field}",
            mapping_pack_id=mapping_pack_id,
            source_field=source_field,
            target_field=target_field,
            status=MappingApprovalStatus.PENDING,
            rationale=rationale,
            reviewed_at=datetime.now(UTC),
        )
        approval.validate()
        return self.mapping_repo.save_approval(approval)

    def approve_mapping(self, approval_id: str, approved_by: str, rationale: str | None = None, approved: bool = True) -> MappingApproval:
        approvals = [a for a in self.mapping_repo._approvals.values() if a.id == approval_id]
        if not approvals:
            raise ValueError("approval not found")
        approval = approvals[0]
        approval.approved_by = approved_by
        approval.rationale = rationale or approval.rationale
        approval.reviewed_at = datetime.now(UTC)
        approval.status = MappingApprovalStatus.APPROVED if approved else MappingApprovalStatus.REJECTED
        return self.mapping_repo.save_approval(approval)

    def list_packs_for_source_type(self, source_type: str) -> list[MappingPack]:
        return self.mapping_repo.list_for_source_type(source_type)

    def list_suggestions(self, pack_id: str) -> list[MappingSuggestion]:
        return self.mapping_repo.list_suggestions_for_pack(pack_id)

    def list_approvals(self, pack_id: str) -> list[MappingApproval]:
        return self.mapping_repo.list_approvals_for_pack(pack_id)

    @staticmethod
    def _ensure_editable(pack: MappingPack) -> None:
        if pack.status != MappingPackStatus.DRAFT:
            raise ValueError("only DRAFT mapping packs can be edited")

    @staticmethod
    def _overlay_priority(pack: MappingPack) -> int:
        priority = {
            "BASE": 0,
            "SOURCE_SYSTEM": 1,
            "CEDING_ADMINISTRATOR": 2,
            "SCHEME": 3,
            "SECTION": 4,
            "BATCH_EXCEPTION": 5,
        }
        return priority[pack.overlay_level.value]
