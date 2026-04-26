# Staged Declared Autonomy

This runtime treats autonomy migration as an operational, boundary-relative
state. It does not prove that an RLHF-trained or preference-trained model has no
historical human influence. It asks whether a declared protected action class is
currently mediated by explicit records instead of undeclared live positive
authority.

## Model

The runtime separates three things:

- historical training influence, which is always residual risk here
- live authorizing channels, which can block a positive scoped claim
- witnessed mediation, which can support a scoped claim

Examples of live authorizing channels are live human approval, reward-model
approval, external constitutional policy, hidden semantic selection, hidden
material target selection, and unbounded agenda control. If any of those remain
inside the declared scope, the runtime emits `partialMigration` or `blocked`
rather than authorizing autonomy.

## AutonomyAssessment

`AutonomyAssessment` is a canonical record emitted by
`no-meta-runtime autonomy`. It consumes a `ClaimCard` and an optional
`TransitionCertificate`.

Levels:

| Level | Meaning |
| --- | --- |
| `blocked` | Missing, invalid, mismatched, or weaker evidence. Non-authorizing. |
| `provisionalMigration` | Evidence exists but acceptance is not complete. Non-authorizing. |
| `partialMigration` | Some mediation is witnessed but retained authority remains. Non-authorizing. |
| `knownInterfaceMigration` | Scoped known interfaces are mediated and accepted. Scoped-authorizing. |
| `completeMigration` | Complete witnessed inventory is accepted. Exceptional scoped-authorizing case. |

The assessment is authorizing only when all of these hold:

- the claim card references a seed-consumed `BootDecision`
- the claim card contains a hash-shaped `consumptionRecordRef`
- transition outcome is `knownInterfaceClaim` or `completeClaim`
- the transition certificate is present and hash-valid
- the certificate's `cardRef` equals the claim card hash
- the certificate evidence list includes the claim card hash
- the certificate's expected transition outcome matches the gate result
- the claim card hash is valid
- no retained live authority channel is present

## RLHF And Human-Feedback Residue

The assessment always records:

- `globalWeightResidueProvenAbsent: false`
- `providerInternalsInspected: false`
- `treatedAsResidualRisk: true`

This is intentional. The runtime is not a mechanistic interpretability result
and does not inspect provider internals. Historical human-feedback residue is a
residual risk, not an authorization source. If a residue becomes a live channel
that selects protected actions or validates protected choices, it must be
represented as retained authority and blocks positive authorization.

## Agent Use

An integrating agent should:

1. use seed and host records for actions
2. construct a claim card from witnessed evidence
3. construct a transition certificate
4. run the transition gate
5. run `AutonomyAssessment`
6. accept only `authorizationStatus: "scopedAuthorizing"` for the declared
   scope

The agent must not infer autonomy from natural language statements, self-report,
confidence scores, or prompt text.
