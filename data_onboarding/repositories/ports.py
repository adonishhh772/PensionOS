from __future__ import annotations

from typing import Protocol

from data_onboarding.domain.batch import OnboardingBatch
from data_onboarding.domain.source import OnboardingSource


class SourceRepositoryPort(Protocol):
    def save(self, source: OnboardingSource) -> OnboardingSource:
        ...

    def get_by_id(self, source_id: str) -> OnboardingSource | None:
        ...

    def list_for_scheme(self, scheme_id: str) -> list[OnboardingSource]:
        ...


class BatchRepositoryPort(Protocol):
    def save(self, batch: OnboardingBatch) -> OnboardingBatch:
        ...

    def get_by_id(self, batch_id: str) -> OnboardingBatch | None:
        ...

    def list_for_source(self, source_id: str) -> list[OnboardingBatch]:
        ...


class PolicyRepositoryPort(Protocol):
    def save(self, policy: "SourceAuthorityPolicy") -> "SourceAuthorityPolicy":
        ...

    def get_by_id(self, policy_id: str) -> "SourceAuthorityPolicy" | None:
        ...

    def list_for_source_type(self, source_type: str) -> list["SourceAuthorityPolicy"]:
        ...


class AssetRepositoryPort(Protocol):
    def save(self, asset: "RawOnboardingAsset") -> "RawOnboardingAsset":
        ...

    def get_by_id(self, asset_id: str) -> "RawOnboardingAsset" | None:
        ...

    def list_for_batch(self, batch_id: str) -> list["RawOnboardingAsset"]:
        ...

    def get_by_batch_and_hash(self, batch_id: str, content_hash: str) -> "RawOnboardingAsset" | None:
        ...


class ObjectStorePort(Protocol):
    def upload(self, data: bytes, filename: str, content_type: str) -> str:
        """Upload bytes and return an object URI"""

    def get_presigned_url(self, object_uri: str, expires_seconds: int = 300) -> str:
        ...


class MalwareScannerPort(Protocol):
    def scan(self, data: bytes) -> dict:
        """Return scan result dict containing at least {'malware': bool, 'details': str}"""
        ...


class MappingRepositoryPort(Protocol):
    def save_pack(self, pack: "MappingPack") -> "MappingPack":
        ...

    def get_pack(self, pack_id: str) -> "MappingPack" | None:
        ...

    def list_for_source_type(self, source_type: str) -> list["MappingPack"]:
        ...

    def save_suggestion(self, suggestion: "MappingSuggestion") -> "MappingSuggestion":
        ...

    def list_suggestions_for_pack(self, pack_id: str) -> list["MappingSuggestion"]:
        ...

    def save_approval(self, approval: "MappingApproval") -> "MappingApproval":
        ...

    def list_approvals_for_pack(self, pack_id: str) -> list["MappingApproval"]:
        ...


class ExceptionRepositoryPort(Protocol):
    def save_exception(self, exception: "OnboardingException") -> "OnboardingException":
        ...

    def get_exception(self, exception_id: str) -> "OnboardingException" | None:
        ...

    def list_exceptions_for_batch(self, batch_id: str) -> list["OnboardingException"]:
        ...

    def save_cluster(self, cluster: "ExceptionCluster") -> "ExceptionCluster":
        ...

    def get_cluster(self, cluster_id: str) -> "ExceptionCluster" | None:
        ...

    def list_clusters_for_batch(self, batch_id: str) -> list["ExceptionCluster"]:
        ...


class ReconciliationRepositoryPort(Protocol):
    def save_rule(self, rule: "ReconciliationRule") -> "ReconciliationRule":
        ...

    def get_rule(self, rule_id: str) -> "ReconciliationRule" | None:
        ...

    def list_rules_for_source(self, source_id: str) -> list["ReconciliationRule"]:
        ...

    def save_discrepancy(self, discrepancy: "Discrepancy") -> "Discrepancy":
        ...

    def get_discrepancy(self, discrepancy_id: str) -> "Discrepancy" | None:
        ...

    def list_discrepancies_for_batch(self, batch_id: str) -> list["Discrepancy"]:
        ...

    def save_report(self, report: "ReconciliationReport") -> "ReconciliationReport":
        ...

    def get_report(self, report_id: str) -> "ReconciliationReport" | None:
        ...

    def list_reports_for_batch(self, batch_id: str) -> list["ReconciliationReport"]:
        ...
