# Changelog

## 0.1.0

- Initial reference runtime scaffold.
- Canonical JSON, SHA-256 record commitments, seed ledger, minimal local host,
  deterministic checkers, transition gate, conformance vectors, documentation,
  and safe local examples.
- Added staged `AutonomyAssessment` records for scoped autonomy migration,
  explicit human-feedback residual-risk handling, certificate/card hash
  verification at the transition gate, and conformance vectors for retained
  authority blocking.
- Tightened public-release semantics: claim cards now validate seed consumption
  evidence, provisional and partial transition claims are explicitly
  non-authorizing, and example envelopes avoid absolute local paths.
- Added strict validation for claim-card subobjects that affect transition
  strength and a Python `is_scoped_authorizing` helper for agent wrappers.
- Tightened transition certificates so positive gate decisions require card
  evidence and a matching expected transition outcome.
