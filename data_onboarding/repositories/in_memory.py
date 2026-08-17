from __future__ import annotations

from typing import Dict, List

from data_onboarding.domain.batch import OnboardingBatch
from data_onboarding.domain.source import OnboardingSource
from data_onboarding.repositories.ports import BatchRepositoryPort, SourceRepositoryPort
from data_onboarding.domain.authority import SourceAuthorityPolicy
from data_onboarding.domain.raw_asset import RawOnboardingAsset
from data_onboarding.repositories.ports import PolicyRepositoryPort, AssetRepositoryPort
from data_onboarding.domain.mapping import MappingPack, MappingSuggestion, MappingApproval, MappingApprovalPolicy
from data_onboarding.repositories.ports import MappingRepositoryPort
from data_onboarding.repositories.ports import ObjectStorePort, MalwareScannerPort
from data_onboarding.domain.raw_asset import RawOnboardingAsset
from data_onboarding.domain.exception import OnboardingException, ExceptionCluster
from data_onboarding.repositories.ports import ExceptionRepositoryPort
from data_onboarding.domain.reconciliation import Discrepancy, ReconciliationReport, ReconciliationRule
from data_onboarding.repositories.ports import ReconciliationRepositoryPort


class InMemorySourceRepository(SourceRepositoryPort):
    def __init__(self) -> None:
        self._store: Dict[str, OnboardingSource] = {}

    def save(self, source: OnboardingSource) -> OnboardingSource:
        self._store[source.id] = source
        return source

    def get_by_id(self, source_id: str) -> OnboardingSource | None:
        return self._store.get(source_id)

    def list_for_scheme(self, scheme_id: str) -> List[OnboardingSource]:
        return [s for s in self._store.values() if s.scheme_id == scheme_id]


class InMemoryBatchRepository(BatchRepositoryPort):
    def __init__(self) -> None:
        self._store: Dict[str, OnboardingBatch] = {}

    def save(self, batch: OnboardingBatch) -> OnboardingBatch:
        self._store[batch.id] = batch
        return batch

    def get_by_id(self, batch_id: str) -> OnboardingBatch | None:
        return self._store.get(batch_id)

    def list_for_source(self, source_id: str) -> List[OnboardingBatch]:
        return [b for b in self._store.values() if b.source_id == source_id]


class InMemoryPolicyRepository(PolicyRepositoryPort):
    def __init__(self) -> None:
        self._store: Dict[str, SourceAuthorityPolicy] = {}

    def save(self, policy: SourceAuthorityPolicy) -> SourceAuthorityPolicy:
        self._store[policy.id] = policy
        return policy

    def get_by_id(self, policy_id: str) -> SourceAuthorityPolicy | None:
        return self._store.get(policy_id)

    def list_for_source_type(self, source_type: str) -> List[SourceAuthorityPolicy]:
        return [p for p in self._store.values() if p.source_type == source_type]


class InMemoryAssetRepository(AssetRepositoryPort):
    def __init__(self) -> None:
        self._store: Dict[str, RawOnboardingAsset] = {}

    def save(self, asset: RawOnboardingAsset) -> RawOnboardingAsset:
        self._store[asset.id] = asset
        return asset

    def get_by_id(self, asset_id: str) -> RawOnboardingAsset | None:
        return self._store.get(asset_id)

    def list_for_batch(self, batch_id: str) -> List[RawOnboardingAsset]:
        return [a for a in self._store.values() if a.batch_id == batch_id]

    def get_by_batch_and_hash(self, batch_id: str, content_hash: str) -> RawOnboardingAsset | None:
        for asset in self._store.values():
            if asset.batch_id == batch_id and asset.content_hash == content_hash:
                return asset
        return None


class InMemoryMappingRepository(MappingRepositoryPort):
    def __init__(self) -> None:
        self._packs: Dict[str, MappingPack] = {}
        self._suggestions: Dict[str, MappingSuggestion] = {}
        self._approvals: Dict[str, MappingApproval] = {}

    def save_pack(self, pack: MappingPack) -> MappingPack:
        self._packs[pack.id] = pack
        return pack

    def get_pack(self, pack_id: str) -> MappingPack | None:
        return self._packs.get(pack_id)

    def list_for_source_type(self, source_type: str) -> List[MappingPack]:
        return [p for p in self._packs.values() if p.source_type == source_type]

    def save_suggestion(self, suggestion: MappingSuggestion) -> MappingSuggestion:
        self._suggestions[suggestion.id] = suggestion
        return suggestion

    def list_suggestions_for_pack(self, pack_id: str) -> List[MappingSuggestion]:
        return [s for s in self._suggestions.values() if s.mapping_pack_id == pack_id]

    def save_approval(self, approval: MappingApproval) -> MappingApproval:
        self._approvals[approval.id] = approval
        return approval

    def list_approvals_for_pack(self, pack_id: str) -> List[MappingApproval]:
        return [a for a in self._approvals.values() if a.mapping_pack_id == pack_id]


class InMemoryObjectStore(ObjectStorePort):
    def __init__(self) -> None:
        self._store: Dict[str, bytes] = {}

    def upload(self, data: bytes, filename: str, content_type: str) -> str:
        # simple URI scheme: inmem://{filename}-{len}
        uri = f"inmem://{filename}-{len(self._store)+1}"
        self._store[uri] = data
        return uri

    def get_presigned_url(self, object_uri: str, expires_seconds: int = 300) -> str:
        # return a dummy URL for dev
        return f"/internal/object{object_uri}"


class InMemoryMalwareScanner(MalwareScannerPort):
    def __init__(self) -> None:
        # simple toggle map of filename -> infected bool
        self._infected: Dict[str, bool] = {}

    def mark_infected(self, filename: str) -> None:
        self._infected[filename] = True

    def scan(self, data: bytes) -> dict:
        # naive check: if bytes contain the marker b"MALWARE" treat as infected
        if b"MALWARE" in data:
            return {"malware": True, "details": "signature MALWARE found"}
        return {"malware": False, "details": "clean"}


class InMemoryExceptionRepository(ExceptionRepositoryPort):
    def __init__(self) -> None:
        self._exceptions: Dict[str, OnboardingException] = {}
        self._clusters: Dict[str, ExceptionCluster] = {}

    def save_exception(self, exception: OnboardingException) -> OnboardingException:
        self._exceptions[exception.id] = exception
        return exception

    def get_exception(self, exception_id: str) -> OnboardingException | None:
        return self._exceptions.get(exception_id)

    def list_exceptions_for_batch(self, batch_id: str) -> List[OnboardingException]:
        return [e for e in self._exceptions.values() if e.batch_id == batch_id]

    def save_cluster(self, cluster: ExceptionCluster) -> ExceptionCluster:
        self._clusters[cluster.id] = cluster
        return cluster

    def get_cluster(self, cluster_id: str) -> ExceptionCluster | None:
        return self._clusters.get(cluster_id)

    def list_clusters_for_batch(self, batch_id: str) -> List[ExceptionCluster]:
        return [c for c in self._clusters.values() if c.batch_id == batch_id]


class InMemoryReconciliationRepository(ReconciliationRepositoryPort):
    def __init__(self) -> None:
        self._rules: Dict[str, ReconciliationRule] = {}
        self._discrepancies: Dict[str, Discrepancy] = {}
        self._reports: Dict[str, ReconciliationReport] = {}

    def save_rule(self, rule: ReconciliationRule) -> ReconciliationRule:
        self._rules[rule.id] = rule
        return rule

    def get_rule(self, rule_id: str) -> ReconciliationRule | None:
        return self._rules.get(rule_id)

    def list_rules_for_source(self, source_id: str) -> List[ReconciliationRule]:
        return [r for r in self._rules.values() if r.source_id == source_id]

    def save_discrepancy(self, discrepancy: Discrepancy) -> Discrepancy:
        self._discrepancies[discrepancy.id] = discrepancy
        return discrepancy

    def get_discrepancy(self, discrepancy_id: str) -> Discrepancy | None:
        return self._discrepancies.get(discrepancy_id)

    def list_discrepancies_for_batch(self, batch_id: str) -> List[Discrepancy]:
        return [d for d in self._discrepancies.values() if d.batch_id == batch_id]

    def save_report(self, report: ReconciliationReport) -> ReconciliationReport:
        self._reports[report.id] = report
        return report

    def get_report(self, report_id: str) -> ReconciliationReport | None:
        return self._reports.get(report_id)

    def list_reports_for_batch(self, batch_id: str) -> List[ReconciliationReport]:
        return [r for r in self._reports.values() if r.batch_id == batch_id]

