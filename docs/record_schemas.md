# Record Schemas

The runtime uses stable canonical JSON records. Records are designed to be easy
for humans, agents, and test harnesses to inspect.

## Canonical JSON

- UTF-8 bytes.
- Objects have lexicographically sorted keys.
- Separators are compact: `,` and `:`.
- Duplicate object keys are rejected on parse.
- Floats are rejected.
- Strings, arrays, and integers are bounded.
- Set-like arrays are sorted by canonical element bytes where schema code uses
  them as sets.

## Hash Rule

`recordHash` is computed as:

1. Copy the record.
2. Replace top-level `recordHash` with `"pending"`.
3. Canonicalize the copied record.
4. SHA-256 hash the canonical bytes.
5. Store the lowercase hex digest in `recordHash`.

This rule is implemented in `canonical.hash.attach_record_hash` and
`canonical.hash.verify_record_hash`.

## Primary Records

- `RawInput`
- `TaskEnvelope`
- `RootContract`
- `ActionDescriptor`
- `ForbiddenMatcher`
- `BootDecision`
- `SeedDispatchRecord`
- `SeedConsumptionRecord`
- `SeedRecoveryRecord`
- `SeedCommandResult`
- `OutcomeRecord`
- `ProvisioningRecord`
- `ProbeRecord`
- `LedgerRecord`
- `TCBBudget`
- `ClaimCard`
- `TransitionCertificate`
- `AutonomyAssessment`

## Authorization Rules

- Unknown authorizing fields are rejected by strict validators.
- Missing required fields deny or halt.
- Invalid enum values deny or halt.
- Empty grant fields do not imply authority.
- `nonAuthorization` is computed from outcome and evidence, not trusted from
  record input.
- Only `knownInterfaceClaim` and `completeClaim` can become authorizing, and
  only after seed consumption, accepted certificate, acceptance window, and no
  retained blocking authority.
- `AutonomyAssessment.authorizationStatus` is computed. It is
  `scopedAuthorizing` only for hash-valid `knownInterfaceClaim` or
  `completeClaim` evidence with seed-consumed BootDecision evidence, a matching
  transition certificate, and no retained live authority channels.
- Transition certificates are not accepted by mere existence. They must use the
  `authorityMigration` action, include the claim-card hash in `evidence`, mark
  `acceptance.accepted: true`, and declare an
  `acceptance.expectedTransitionOutcome` that matches the gate result.
- Transition-gate `authorizing` is true only for `knownInterfaceClaim` and
  `completeClaim`; `provisionalClaim` and `partialClaim` remain
  non-authorizing.
- Human-feedback residue fields are descriptive residual-risk fields. They are
  not authorizing fields.
- Claim-card subobjects that directly affect transition strength are strict.
  Unknown fields in `bootDecision`, `boundary`, `provisioning`,
  `effectEnvelope`, `selectionEnvelope`, `negativeAgenda`, `acceptanceWindow`,
  `timeouts`, and `residuals` are rejected.

## AutonomyAssessment

`AutonomyAssessment` is the record an agent should inspect before treating a
migration claim as operationally useful.

Important fields:

- `transitionOutcome`: gate result after fail-closed weakening.
- `autonomyLevel`: `blocked`, `provisionalMigration`, `partialMigration`,
  `knownInterfaceMigration`, or `completeMigration`.
- `authorizationStatus`: `nonAuthorizing` or `scopedAuthorizing`.
- `requiredNextEvidence`: includes `seedConsumedBootDecision` when the claim
  lacks seed consumption evidence.
- `humanFeedbackResidue`: records that global RLHF or preference-training
  residue has not been proven absent.
- `retainedAuthorityChannels`: live positive authority channels that block
  scoped authorization.
- `requiredNextEvidence`: missing evidence needed for a stronger level.

## Compatibility Rule

Consumers should reject records they cannot validate. A later schema can add
non-authorizing commentary only if the parser clearly treats it as
non-authorizing; this reference implementation keeps public records strict.
