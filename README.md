# WebClaimVerifier

A reusable GenLayer Intelligent Contract for decentralized verification of real-world web claims.

## Why this primitive?

Traditional smart contracts cannot directly evaluate dynamic, unstructured web information. WebClaimVerifier turns that problem into a consensus-critical contract operation.

A user submits:

- a claim
- a public source URL
- a unique claim ID

A GenLayer leader independently fetches the source and evaluates the claim with an LLM. Validators independently repeat the source retrieval and evaluation, then verify the leader result through a custom equivalence rule.

The accepted result is written to contract state only after consensus.

## Consensus design

The contract deliberately does **not** compare free-form reasoning text.

Validators compare stable decision fields:

1. `decision` must match exactly.
2. `confidence` may differ by at most 15 points.
3. `VERIFIED` and `REJECTED` require at least 60 confidence.
4. Evidence text is stored but is not required to be word-for-word equivalent.

This follows the GenLayer Equivalence Principle: independent validators should verify the substance of the leader's result rather than merely checking its formatting.

## State

Each verified claim stores:

```text
claim
source_url
decision
confidence
evidence
```

Possible decisions:

- `VERIFIED`
- `REJECTED`
- `DISPUTED`

## Contract API

### `verify_claim(claim_id, claim, source_url)`

Fetches the source, evaluates the claim, runs leader/validator consensus, and stores the accepted result.

### `get_claim(claim_id)`

Returns the stored verification result.

## Example

```python
contract.verify_claim(
    "sec-001",
    "The SEC approved the XYZ filing.",
    "https://example.com/source"
)
```

A successful consensus result might be:

```json
{
  "decision": "VERIFIED",
  "confidence": 91,
  "evidence": "The source explicitly states that the filing was approved."
}
```

## Use cases

The primitive can be reused for:

- regulatory and compliance claims
- public announcements
- event verification
- news-source verification
- DAO governance evidence
- reputation systems
- prediction-market resolution inputs
- decentralized information registries

## Security considerations

The contract does not treat the leader as trusted. Every validator independently evaluates the source and claim.

Source content is truncated before being sent to the model to reduce unnecessary computation and storage pressure. Applications using this primitive should also consider source allowlists, URL reputation, archival sources, and prompt-injection defenses for production deployments.

## Testing

The project is designed for the GenLayer Testing Suite.

```bash
pip install genlayer-test pytest
gltest tests/ -v
```

For local Studio integration:

```bash
genlayer up
gltest tests/ --network studionet
```

## Project status

MVP Intelligent Contract primitive. No frontend is required; the contract is intended to be imported or integrated by other builders.
