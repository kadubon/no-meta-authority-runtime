# Architecture

This repository implements the paper's executable, fail-closed path as a set of
small modules with explicit boundaries. The goal is not to create a broad
autonomous authority system; it is to provide a reference runtime that can be
audited, replayed, tested, and embedded.

## Concept Mapping

| Paper concept | Runtime module |
| --- | --- |
| Canonical bytes and SHA-256 commitments | `canonical.json`, `canonical.hash` |
| Active schema constants and record limits | `schemas.constants` |
| BootDecision | `schemas.boot_decision` |
| Action descriptor | `schemas.action` |
| Task envelope and root contract placeholder | `schemas.task_envelope` |
| Outcome record | `schemas.outcome` |
| Probe record | `schemas.probe` |
| Provisioning record | `schemas.provisioning` |
| TCB budget | `schemas.tcb` |
| Claim card and certificate | `schemas.certificate`, `cert.*` |
| Default forbidden matchers | `matchers.default_matchers` |
| Matcher grammar | `matchers.forbidden` |
| Literal path policy | `matchers.path_policy` |
| Seed interpreter | `seed.interpreter` |
| Seed command interface | `seed.cli` |
| Seed ledger state machine | `seed.state_machine` |
| Append-only ledger | `ledger.append_only`, `ledger.head`, `ledger.recovery`, `ledger.locks` |
| Minimal local host | `host.minimal_host` |
| Host rollback, probes, digest | `host.rollback`, `host.probes`, `host.digest` |
| Micro-predicates | `checkers.*` |
| Transition gate | `gate.claim_evaluator`, `gate.transition_gate` |
| Staged declared autonomy assessment | `autonomy.assessment`, `schemas.autonomy` |
| Conformance vectors | `conformance.*` |

## Data Flow

```text
TaskEnvelope
  -> ActionDescriptor
  -> BootDecision
  -> SeedInterpreter
      -> forbidden matchers
      -> append-only seed ledger
      -> dispatch / terminal consumption
  -> MinimalHost
      -> boot
      -> prepare
      -> check
      -> commit
      -> recover
      -> digest
  -> ClaimCard
  -> TransitionCertificate
  -> TransitionGate
  -> AutonomyAssessment
```

## Fail-Closed Boundaries

- If parsing fails, the caller receives a weaker outcome.
- If a forbidden matcher matches, seed dispatch stops before invocation.
- If a ledger branch is ambiguous, positive claims are blocked.
- If a host root is not declared, the host does not create files.
- If an operation path is outside `grantedWriteRoots`, the host halts.
- If rollback data is missing, commit is not certified.
- If inventory is incomplete, `completeClaim` is blocked.
- If an interface is unknown, the outcome weakens.
- If claim or certificate hashes do not verify, the transition gate halts.
- If seed consumption evidence is missing, positive autonomy assessment is
  deferred and non-authorizing.
- If the transition outcome is `provisionalClaim` or `partialClaim`, the gate
  marks it non-authorizing even when the claim form is accepted.
- If live human-feedback, semantic, selector, or agenda authority remains in the
  declared scope, `AutonomyAssessment` is non-authorizing.

## Staged Autonomy Mapping

The paper's migration vision is represented as a conservative staged assessment,
not as a global proof of self-originating agency. `AutonomyAssessment` maps a
valid transition gate result into one of:

- `blocked`
- `provisionalMigration`
- `partialMigration`
- `knownInterfaceMigration`
- `completeMigration`

Only `knownInterfaceMigration` and `completeMigration` can be
`scopedAuthorizing`. Historical RLHF or preference-training residue is always
recorded as residual risk unless stronger independent evidence is supplied; it
does not become authorization merely because an agent describes itself as
autonomous.

## Deliberate Limits

The implementation supports a local reversible class by default. It models but
does not authorize network calls, credentials, external writes, public output,
delegation, memory writes, checker updates, kernel updates, or irreversible
information release.

This is a reference TCB, not a proof of global hidden-channel absence.
