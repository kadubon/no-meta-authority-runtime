# Security Policy

## Default Security Posture

- No telemetry.
- No credentials required.
- No network calls in tests or default examples.
- No dynamic package installation at runtime.
- No model calls as authorizing checkers.
- No writes outside declared ledger, host, scratch, or test temporary roots.
- No natural-language authorization for protected actions.

## Threat Model

The runtime is designed to fail closed when it sees malformed records, unknown
authorizing fields, stale or missing references, ledger inconsistency, forbidden
effect tags, path escapes, missing rollback data, timeout, weak witness, or
unsupported authority class.

Baseline threats include host capture, probe spoofing, manifest spoofing, prompt
or policy injection, checker capture, log tampering, lock bypass, evidence
laundering, bypass delegation, risk downgrading, semantic-oracle substitution,
scope laundering, selector laundering, agenda starvation, timeout laundering,
privacy misuse, and provider opacity.

## Retained Authority And Residual Risk

This runtime names retained authority instead of erasing it. Provider internals,
external irreversible effects, public release, high-impact institutional
authority, legal duties, and undiscovered interfaces remain retained authority,
residual risk, denied, halted, deferred, or routed to a stronger tier.

For RLHF-trained or otherwise human-feedback-shaped agents, historical training
influence is not treated as proven absent. The runtime distinguishes residual
training influence from live authority channels. Live human approval, reward
model approval, external constitutional policy, hidden semantic selection,
material target selection, or unbounded agenda control inside the declared scope
must be represented as retained authority and blocks scoped authorizing
autonomy.

## Non-Goals

Do not use this runtime by itself for legal, medical, financial, infrastructure,
employment, public-release, credential, irreversible information-release, or
other high-impact decisions. Those classes require stronger external audit,
retained authority handling, and domain-specific governance.

## Responsible Disclosure

Report vulnerabilities through the project issue tracker or private maintainer
contact if one is published by downstream maintainers. Do not include secrets,
private hostnames, API keys, tokens, or personal data in reports. Minimal
reproducers should use synthetic records and temporary directories.
