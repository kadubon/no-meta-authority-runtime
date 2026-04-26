# seed_only

Runs a seed-only safe inventory flow in a temporary directory. It issues one
`BootDecision`, dispatches one `safeInventory` action, consumes it, and prints
the digest. No network or credentials are used.

```bash
uv run python examples/seed_only/run_seed_demo.py
```
