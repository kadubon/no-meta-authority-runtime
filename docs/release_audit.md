# Release Audit

This checklist is intended for maintainers before publishing a source archive,
package, or repository mirror.

## Required Commands

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
uv run no-meta-seed --help
uv run no-meta-runtime --help
uv run no-meta-runtime conformance
uv run python examples/seed_only/run_seed_demo.py
uv run python examples/local_reversible_patch/run_example.py
uv run python examples/agent_wrapper_mock/mock_agent.py
```

## Security Checks

- No credentials, API keys, tokens, private hostnames, personal paths, or
  environment-specific identifiers in tracked files.
- No tests or examples requiring network access.
- No runtime package installation.
- No hidden telemetry.
- No writes outside temporary directories or declared local roots.
- No `provisionalClaim` or `partialClaim` treated as authorizing.
- No `ClaimCard` treated as authorizing without seed-consumption evidence.
- No positive autonomy assessment without hash-valid card and certificate.
- No transition certificate accepted without card evidence and matching expected
  transition outcome.

Run a local text scan for common secret names, platform-specific absolute
paths, private-key headers, and environment-specific identifiers before release.

## Overclaiming Checks

- The project must not claim global absence of RLHF or human-feedback residue.
- The project must not claim provider internals were inspected.
- The project must not claim legal, medical, financial, infrastructure,
  employment, credential, public-release, or irreversible information-release
  authority.
- `completeClaim` must remain exceptional and witness-dependent.

## Expected Public Position

The project is a reference runtime for scoped, witnessed, seed-mediated,
fail-closed authority migration. It is not a global proof of autonomous moral,
legal, or metaphysical legitimacy.
