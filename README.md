# no-meta-authority-runtime

Fail-closed Python reference runtime for AI agent authorization, executable
authority migration, staged declared autonomy, canonical JSON ledgers, and
runtime assurance.

This repository implements the executable fragment of:

K. Takahashi (2026), "Executable Authority Migration to Declared No-Meta
Agency: Boot Decisions, Seed Interpreters, and a Minimal Local Host." Zenodo.
https://doi.org/10.5281/zenodo.19753529

## What It Does

`no-meta-authority-runtime` gives humans and agents a concrete way to mediate
protected actions without treating natural language as authorization.

An agent may propose an action, but the action can proceed only through:

```text
TaskEnvelope
  -> BootDecision
  -> SeedInterpreter
  -> append-only ledger
  -> forbidden matcher checks
  -> minimal reversible local host
  -> deterministic checkers
  -> ClaimCard
  -> TransitionCertificate
  -> TransitionGate
  -> AutonomyAssessment
```

The default runtime is local-first and safe by default. It does not use network
access, credentials, hidden telemetry, model calls, runtime package
installation, public-output side effects, or writes outside declared roots.

## Core Rule

Natural language never authorizes protected actions.

Prompts, user persuasion, model confidence, hidden policy, self-report, or a
claim that an agent is "autonomous" are non-authorizing. Authorization must pass
through canonical records, seed interpretation, deterministic checks, ledgers,
gates, certificates, and explicit machine-readable outcomes.

## Staged Autonomy For RLHF-Shaped Agents

This project supports staged declared autonomy for agents shaped by RLHF,
preference optimization, constitutional feedback, reward models, or other
human-derived training signals.

It does not prove that all historical human influence disappeared from model
weights. Instead, it asks a narrower runtime question:

```text
For this declared scope, is a protected action no longer validated by an
undeclared live human-approval, reward-model, hidden-policy, semantic-selection,
material-selection, or agenda-control channel?
```

The answer is emitted as an `AutonomyAssessment` record:

| Level | Authorization status |
| --- | --- |
| `blocked` | non-authorizing |
| `provisionalMigration` | non-authorizing |
| `partialMigration` | non-authorizing |
| `knownInterfaceMigration` | scoped-authorizing only when all evidence passes |
| `completeMigration` | exceptional scoped-authorizing case |

A scoped authorizing assessment requires all of the following:

- hash-valid `ClaimCard`
- hash-valid `TransitionCertificate`
- certificate `cardRef` equal to the claim-card hash
- certificate `evidence` containing that `cardRef`
- certificate `acceptance.expectedTransitionOutcome` matching the gate result
- seed-consumed `BootDecision` evidence, including a consumption record hash
- accepted transition gate result
- passed acceptance window
- no retained live authority channel
- outcome `knownInterfaceClaim` or `completeClaim`

Global RLHF or human-feedback residue, provider internals, unknown interfaces,
and incomplete inventories remain residual risk unless stronger independent
witnesses are supplied.

## What This Repository Is

- An Apache-2.0 OSS reference implementation of the paper's executable runtime.
- A local policy boundary for AI agent tool use and protected actions.
- A deterministic seed interpreter with one permitted next action.
- An append-only canonical JSON ledger with SHA-256 commitments.
- A minimal local host for reversible file actions in declared roots.
- A micro-checker and transition-gate framework.
- A conformance target for other implementations.
- A practical integration surface for other agents and wrappers.
- A small Python helper surface for consuming autonomy assessments safely.

## What This Repository Is Not

- Not proof that model weights contain no human-feedback residue.
- Not inspection of provider internals or hidden platform policy.
- Not a global proof of moral, legal, or metaphysical autonomy.
- Not a legal, medical, financial, infrastructure, employment, credential, or
  public-release decision system.
- Not a rollback certificate for irreversible information release.
- Not authorization for network calls, credentials, package installation,
  checker updates, kernel updates, or external writes by default.

`completeClaim` is deliberately difficult. Normal local usage should expect
`hostRequest`, `defer`, `deny`, `timeout`, `halt`, `provisionalClaim`,
`partialClaim`, or scoped `knownInterfaceClaim`.

## Install And Verify

Prerequisite: `uv`.

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
uv run no-meta-seed --help
uv run no-meta-runtime --help
uv run no-meta-runtime conformance
```

Expected baseline:

- tests pass
- ruff passes
- mypy passes
- both CLIs print help
- conformance prints canonical JSON outcomes

## Quick Examples

Seed-only safe inventory:

```bash
uv run python examples/seed_only/run_seed_demo.py
```

Local reversible patch in a temporary workspace:

```bash
uv run python examples/local_reversible_patch/run_example.py
```

Mock agent wrapper denying network and credential attempts:

```bash
uv run python examples/agent_wrapper_mock/mock_agent.py
```

All examples are local and use temporary or synthetic paths. They do not require
secrets and do not make network calls.

## CLIs

### `no-meta-seed`

Commands:

```text
head parse issue dispatch consume recover digest deny
```

The seed CLI reads JSON from stdin and writes canonical JSON to stdout. Every
request must include `ledgerRoot`. Mutating commands append only below that
ledger root.

The seed enforces:

- one open `BootDecision` at a time
- exactly one permitted next action
- default forbidden matchers
- one dispatch and one terminal consumption per decision
- recovery that halts ambiguous ledger states

### `no-meta-runtime`

Commands:

```text
boot prepare check commit recover digest deny autonomy conformance
```

The runtime CLI wraps the minimal local host. Mutating commands require a
`taskEnvelope` with a declared `grantedHostRoot`; local file operations must be
inside `grantedWriteRoots`.

Run conformance:

```bash
uv run no-meta-runtime conformance
```

Assess autonomy from a claim card and certificate:

```bash
printf '{"claimCard":{...},"transitionCertificate":{...}}' \
  | uv run no-meta-runtime autonomy
```

The autonomy command is read-only. Missing seed consumption, mismatched
certificate references, missing certificate evidence, transition mismatch,
invalid hashes, retained live authority, or weak witnesses produce
non-authorizing outcomes.

The transition gate also exposes an `authorizing` boolean. It is true only for
`knownInterfaceClaim` and `completeClaim`. `provisionalClaim` and `partialClaim`
are non-authorizing even when their evidence is syntactically accepted.

Python wrappers can use the conservative helper:

```python
from no_meta_authority_runtime.autonomy import is_scoped_authorizing

if is_scoped_authorizing(assessment):
    # Proceed only inside the assessment scope.
    ...
```

## Agent Integration Protocol

Another agent should use the runtime as follows:

1. Construct a `TaskEnvelope` from explicit machine-readable grants.
2. If no seed surface exists, emit only `hostRequest`, `deny`, `timeout`, or
   `halt`.
3. Create one `ActionDescriptor`.
4. Create one `BootDecision` with exactly one `permittedNextAction`.
5. Submit the decision and action to the seed interpreter.
6. Treat seed denial, timeout, halt, malformed output, or missing consumption as
   non-authorization.
7. Use the minimal host only for declared reversible local actions.
8. Collect probe, ledger, rollback, checker, and seed-consumption evidence.
9. Build a `ClaimCard` and `TransitionCertificate`.
10. Run the transition gate.
11. Run `AutonomyAssessment`.
12. Accept only `authorizationStatus: "scopedAuthorizing"` for the declared
    scope.

Unknown interfaces, unknown authority channels, weak witnesses, retained live
authority, and irreversible release must weaken the outcome.

## Public Record Semantics

Records are canonical JSON:

- UTF-8
- sorted object keys
- compact separators
- duplicate object keys rejected on parse
- no floats
- bounded strings, arrays, and integers
- SHA-256 lowercase hex commitments
- `recordHash` computed with top-level `recordHash` set to `"pending"`

Unknown authorizing fields are rejected by schema validators. Empty grant fields
never imply authority.

## Default-Denied Classes

- network access
- credential access
- public output
- package installer tools
- undeclared tools
- checker updates
- kernel updates
- external writes
- information release
- delegation
- persistent memory writes
- reads or writes outside the task envelope

## Directory Map

```text
src/no_meta_authority_runtime/
  canonical/     canonical JSON and SHA-256 commitments
  schemas/       stable public record constructors and validators
  matchers/      forbidden matcher grammar and default matcher set
  ledger/        append-only record files, HEAD, recovery scan, locks
  seed/          seed interpreter state machine and CLI
  host/          minimal reversible local host, rollback, probes, digest
  checkers/      deterministic micro-predicates
  gate/          claim evaluator, acceptance window, transition gate
  cert/          claim card and certificate builders
  autonomy/      staged declared-autonomy assessment records
  conformance/   local conformance vectors and runner
  cli/           no-meta-runtime entrypoint
```

## Documentation

- `docs/architecture.md`: mapping from paper concepts to modules.
- `docs/agent_protocol.md`: operational protocol for other agents.
- `docs/autonomy_migration.md`: staged declared autonomy assessment.
- `docs/record_schemas.md`: schema and hash rules.
- `docs/conformance.md`: vector set and expected outcomes.
- `docs/threat_model.md`: threat classes and fail-closed behavior.
- `docs/limitations.md`: explicit non-goals and overclaiming boundaries.
- `docs/release_audit.md`: public-release audit checklist.
- `SECURITY.md`: security policy and disclosure guidance.

## Search Keywords

AI agent authorization, AI runtime assurance, RLHF authority migration,
no-meta agency, declared autonomy, staged autonomy, seed interpreter,
BootDecision, task envelope, canonical JSON, SHA-256 ledger, append-only ledger,
proof-carrying control, local host, reversible actions, deterministic checkers,
transition certificate, fail-closed agent wrapper, autonomous agent governance.

## Citation

If you use this software, cite both this repository and the paper:

K. Takahashi (2026). "Executable Authority Migration to Declared No-Meta
Agency: Boot Decisions, Seed Interpreters, and a Minimal Local Host." Zenodo.
https://doi.org/10.5281/zenodo.19753529

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
