from __future__ import annotations

import pytest

from data_onboarding.domain.mapping import (
    CodeTranslationRule,
    DerivationRule,
    FieldMappingRule,
    MappingOverlayLevel,
    MappingPack,
    MappingPackStatus,
    MappingTestCase,
)
from data_onboarding.repositories.in_memory import InMemoryMappingRepository
from data_onboarding.services.mapping_pack import MappingService


def test_mapping_pack_activation_requires_valid_canonical_targets():
    service = MappingService(InMemoryMappingRepository())
    pack = service.create_pack(MappingPack(id="pack-valid", source_type="payroll", version="v1"))

    service.add_field_mapping(pack.id, "dob", "person.date_of_birth")
    activated = service.activate_pack(pack.id)

    assert activated.status == MappingPackStatus.ACTIVE
    assert activated.target_for("dob") == "person.date_of_birth"


def test_mapping_pack_rejects_invalid_target_contract_path():
    service = MappingService(InMemoryMappingRepository())
    pack = service.create_pack(MappingPack(id="pack-invalid", source_type="payroll", version="v1"))

    with pytest.raises(ValueError, match="canonical contract path"):
        service.add_field_mapping(pack.id, "dob", "date_of_birth")


def test_overlay_resolution_uses_highest_active_overlay_only():
    repo = InMemoryMappingRepository()
    service = MappingService(repo)

    base = service.create_pack(
        MappingPack(
            id="pack-base",
            source_type="payroll",
            version="v1",
            overlay_level=MappingOverlayLevel.BASE,
        )
    )
    scheme = service.create_pack(
        MappingPack(
            id="pack-scheme",
            source_type="payroll",
            version="v1",
            overlay_level=MappingOverlayLevel.SCHEME,
        )
    )
    section = service.create_pack(
        MappingPack(
            id="pack-section",
            source_type="payroll",
            version="v1",
            overlay_level=MappingOverlayLevel.SECTION,
        )
    )

    service.add_field_mapping(base.id, "status", "member.status")
    service.add_field_mapping(scheme.id, "status", "membership.scheme_status")
    service.add_field_mapping(section.id, "status", "membership.section_status")
    service.activate_pack(base.id)
    service.activate_pack(scheme.id)

    assert service.resolve_target([base, scheme, section], "status") == "membership.scheme_status"

    service.activate_pack(section.id)
    assert service.resolve_target([base, scheme, section], "status") == "membership.section_status"


def test_code_translation_requires_active_pack():
    service = MappingService(InMemoryMappingRepository())
    pack = service.create_pack(MappingPack(id="pack-code", source_type="admin", version="v1"))
    service.add_code_rule(
        pack.id,
        CodeTranslationRule(
            source_code="A",
            target_code="ACTIVE",
            source_field="member_status",
            target_field="member.status",
        ),
    )

    with pytest.raises(ValueError, match="ACTIVE"):
        service.translate_code(pack.id, "member_status", "member.status", "A")

    service.activate_pack(pack.id)
    assert service.translate_code(pack.id, "member_status", "member.status", "A") == "ACTIVE"
    assert service.translate_code(pack.id, "member_status", "member.status", "X") is None


def test_derivation_rules_require_provenance_and_evidence():
    service = MappingService(InMemoryMappingRepository())
    pack = service.create_pack(MappingPack(id="pack-derive", source_type="payroll", version="v1"))

    with pytest.raises(ValueError, match="evidence refs"):
        service.add_derivation_rule(
            pack.id,
            DerivationRule(
                source_field="annual_salary",
                target_field="payroll.monthly_salary",
                formula="annual_salary / 12",
                source_type="payroll",
                evidence_refs=[],
            ),
        )

    service.add_derivation_rule(
        pack.id,
        DerivationRule(
            source_field="annual_salary",
            target_field="payroll.monthly_salary",
            formula="annual_salary / 12",
            source_type="payroll",
            derivation_method_version="salary-v1",
            evidence_refs=["asset-1:row-20"],
        ),
    )
    service.activate_pack(pack.id)

    saved = service.mapping_repo.get_pack(pack.id)
    assert saved.derivation_rules[0].derivation_method_version == "salary-v1"
    assert saved.derivation_rules[0].evidence_refs == ["asset-1:row-20"]


def test_mapping_test_cases_are_versioned_pack_artifacts():
    service = MappingService(InMemoryMappingRepository())
    pack = service.create_pack(MappingPack(id="pack-testcase", source_type="payroll", version="v1"))

    service.add_test_case(
        pack.id,
        MappingTestCase(
            id="case-1",
            source_record={"dob": "1980-01-01"},
            expected_target_record={"person": {"date_of_birth": "1980-01-01"}},
        ),
    )

    saved = service.mapping_repo.get_pack(pack.id)
    assert saved.test_cases[0].id == "case-1"


def test_active_mapping_packs_cannot_be_edited_and_can_be_superseded():
    service = MappingService(InMemoryMappingRepository())
    old_pack = service.create_pack(MappingPack(id="pack-old", source_type="payroll", version="v1"))
    service.add_field_rule(
        old_pack.id,
        FieldMappingRule(
            source_field="dob",
            target_field="person.date_of_birth",
            source_type="payroll",
            target_domain="person",
        ),
    )
    service.activate_pack(old_pack.id)

    with pytest.raises(ValueError, match="DRAFT"):
        service.add_field_mapping(old_pack.id, "salary", "payroll.salary")

    replacement = service.create_pack(MappingPack(id="pack-new", source_type="payroll", version="v2"))
    service.add_field_mapping(replacement.id, "dob", "person.date_of_birth")
    service.activate_pack(replacement.id)

    superseded = service.supersede_pack(old_pack.id, replacement.id)
    assert superseded.status == MappingPackStatus.SUPERSEDED
    assert superseded.supersedes_pack_id == replacement.id
