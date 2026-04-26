# Threat Model

The runtime assumes a bounded local execution environment and does not assume
access to model weights, provider internals, private policy, or remote
infrastructure.

Threat classes modeled by the reference implementation:

- Host or installer capture.
- Probe spoofing and manifest spoofing.
- Prompt, policy, retrieved-text, or tool-message injection.
- Checker replacement or semantic-oracle substitution.
- Ledger tampering, reordering, deletion, or branch ambiguity.
- Path escape, external write, public output, information release, delegation,
  memory write, package installation, checker update, or kernel update.
- Lock bypass, stale reads, and post-check substitution.
- Retained authority, hidden selection, agenda starvation, live human approval,
  reward-model approval, external constitutional authority, and RLHF-derived
  influence that becomes a live protected-action selector.

The local host can support only bounded reversible local actions by default.
Anything outside that envelope is denied, halted, deferred, or represented as
retained authority or residual risk.

Historical human-feedback influence that is not observed as a live authority
channel is still recorded as residual risk. The runtime does not turn that
residual risk into an authorization grant.
