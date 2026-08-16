# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class WebClaimVerifier(gl.Contract):
    claims: dict

    def __init__(self):
        self.claims = {}

    @gl.public.write
    def verify_claim(self, claim_id: str, claim: str, source_url: str) -> dict:
        if not claim_id or not claim:
            raise gl.UserError("claim_id and claim are required")
        if not source_url.startswith(("http://", "https://")):
            raise gl.UserError("source_url must use http:// or https://")
        if claim_id in self.claims:
            raise gl.UserError("claim_id already exists")

        def evaluate_claim():
            response = gl.nondet.web.get(source_url)
            source_text = response.body.decode("utf-8")

            prompt = f"""
You are a decentralized web-claim verifier.

Claim:
{claim}

Source URL:
{source_url}

Source content:
{source_text[:12000]}

Determine whether the source supports the claim.

Return JSON with exactly:
{{
  "decision": "VERIFIED" | "REJECTED" | "DISPUTED",
  "confidence": integer from 0 to 100,
  "evidence": "short explanation grounded only in the source"
}}

Rules:
- VERIFIED only when the source provides sufficient evidence supporting the claim.
- REJECTED when the source clearly contradicts the claim.
- DISPUTED when the source is insufficient, ambiguous, or contradictory.
- Do not use outside knowledge.
"""
            result = gl.nondet.exec_prompt(prompt, response_format="json")

            if not isinstance(result, dict):
                raise gl.UserError("LLM returned a non-object result")

            decision = result.get("decision")
            confidence = result.get("confidence")
            evidence = result.get("evidence")

            if decision not in ("VERIFIED", "REJECTED", "DISPUTED"):
                raise gl.UserError("invalid decision")
            if not isinstance(confidence, int) or not 0 <= confidence <= 100:
                raise gl.UserError("invalid confidence")
            if not isinstance(evidence, str) or not evidence.strip():
                raise gl.UserError("missing evidence")

            return {
                "decision": decision,
                "confidence": confidence,
                "evidence": evidence.strip(),
            }

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False

            leader = leader_result.calldata

            try:
                independent = evaluate_claim()
            except Exception:
                return False

            # Consensus-critical fields must agree exactly.
            # Evidence wording may differ between validators.
            if independent["decision"] != leader["decision"]:
                return False

            # Allow small model variation while preventing a materially
            # different confidence score from being accepted.
            if abs(independent["confidence"] - leader["confidence"]) > 15:
                return False

            # A rejection or verification requires meaningful confidence.
            if leader["decision"] in ("VERIFIED", "REJECTED"):
                if leader["confidence"] < 60 or independent["confidence"] < 60:
                    return False

            return True

        result = gl.vm.run_nondet_unsafe(evaluate_claim, validator_fn)

        self.claims[claim_id] = {
            "claim": claim,
            "source_url": source_url,
            "decision": result["decision"],
            "confidence": result["confidence"],
            "evidence": result["evidence"],
        }

        return self.claims[claim_id]

    @gl.public.view
    def get_claim(self, claim_id: str) -> dict:
        if claim_id not in self.claims:
            raise gl.UserError("claim not found")
        return self.claims[claim_id]
