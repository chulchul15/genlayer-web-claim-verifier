import pytest
from genlayer import gl
from gltest import get_contract_factory


def test_initial_state(direct_deploy):
    contract = direct_deploy("contracts/WebClaimVerifier.py")
    with pytest.raises(Exception):
        contract.get_claim("missing")


def test_verify_claim_stores_consensus_result(direct_vm, direct_deploy):
    direct_vm.mock_web(
        "https://example.com/fact",
        body="GenLayer is an AI-native blockchain for Intelligent Contracts.",
    )
    direct_vm.mock_llm(
        r".*",
        {
            "decision": "VERIFIED",
            "confidence": 92,
            "evidence": "The source explicitly states that GenLayer is an AI-native blockchain for Intelligent Contracts.",
        },
    )

    contract = direct_deploy("contracts/WebClaimVerifier.py")
    result = contract.verify_claim(
        "claim-1",
        "GenLayer is an AI-native blockchain for Intelligent Contracts.",
        "https://example.com/fact",
    )

    assert result["decision"] == "VERIFIED"
    assert result["confidence"] == 92
    assert contract.get_claim("claim-1")["source_url"] == "https://example.com/fact"


def test_duplicate_claim_id_reverts(direct_deploy):
    contract = direct_deploy("contracts/WebClaimVerifier.py")
    with pytest.raises(Exception):
        contract.verify_claim("", "A claim", "https://example.com")


def test_validator_rejects_materially_different_decision(direct_vm, direct_deploy):
    direct_vm.mock_web(
        "https://example.com/fact",
        body="The source supports the claim.",
    )
    direct_vm.mock_llm(
        r".*",
        {
            "decision": "VERIFIED",
            "confidence": 90,
            "evidence": "Supported.",
        },
    )

    contract = direct_deploy("contracts/WebClaimVerifier.py")
    contract.verify_claim(
        "claim-2",
        "The source supports the claim.",
        "https://example.com/fact",
    )

    direct_vm.clear_mocks()
    direct_vm.mock_web(
        "https://example.com/fact",
        body="The source supports the claim.",
    )
    direct_vm.mock_llm(
        r".*",
        {
            "decision": "REJECTED",
            "confidence": 90,
            "evidence": "Contradicted.",
        },
    )

    assert direct_vm.run_validator() is False
