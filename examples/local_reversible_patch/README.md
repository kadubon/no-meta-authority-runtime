# local_reversible_patch

Creates a temporary workspace, declares it as the only write root, prepares a
small text-file write, checks deterministic predicates, commits the write, and
builds a known-interface-style local certificate plus an `AutonomyAssessment`.
The example first issues and dispatches a seed-mediated `safeInventory`
BootDecision, so the assessment can reference a seed record. The assessment is
scoped to the temporary workspace and does not claim global absence of RLHF or
human-feedback residue.

```bash
uv run python examples/local_reversible_patch/run_example.py
```
