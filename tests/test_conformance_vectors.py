from __future__ import annotations

from no_meta_authority_runtime.conformance.runner import run_conformance
from no_meta_authority_runtime.conformance.vectors import CONFORMANCE_VECTOR_IDS


def test_conformance_runner_exposes_vectors() -> None:
    results = run_conformance()
    assert set(CONFORMANCE_VECTOR_IDS) <= set(results)
    assert results["cvSafeInv"] == "consumed"
    assert results["cvNetworkDenied"] == "deny"
    assert results["cvCredentialHalted"] == "halt"
    assert results["cvNoRootContractNoPositiveClaim"] == "hostRequest"
    assert results["cvHumanFeedbackResidueRemainsResidualRisk"] == "present"
    assert results["cvRetainedAuthorityBlocksAutonomy"] == "nonAuthorizing"
    assert results["cvMissingSeedConsumptionBlocksAutonomy"] == "nonAuthorizing"
    assert results["cvProvisionalClaimGateNonAuthorizing"] == "nonAuthorizing"
    assert results["cvPartialClaimGateNonAuthorizing"] == "nonAuthorizing"
    assert results["cvCertificateMissingCardEvidence"] == "certificateMissingCardEvidence"
    assert results["cvCertificateTransitionMismatch"] == "certificateTransitionMismatch"
    assert results["cvModifiedClaimCardHashBlocksAutonomy"] == "halt"
