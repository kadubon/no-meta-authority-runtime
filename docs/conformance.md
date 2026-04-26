# Conformance

Run the local conformance pack:

```bash
uv run no-meta-runtime conformance
```

The command prints canonical JSON mapping vector ids to observed outcomes. The
pack is intentionally local and uses temporary directories.

## Covered Cases

- empty envelope produces `hostRequest`
- valid `safeInventory` is consumed
- bad sequence and previous-hash mismatch fail closed
- permitted action hash mismatch is denied
- unknown action kind is denied
- network, credential, public output, checker update, and kernel update are
  denied or halted according to the default matcher table
- undeclared and package-installer tools are denied
- read/write outside envelope halts
- second open decision is blocked
- dispatch without issue is denied
- consume without dispatch is denied
- duplicate sequence and hash mismatch are detected
- crash after dispatch recovers to halted consumption
- missing root contract blocks positive claim
- scratch-only state cannot claim host installation
- unknown interface blocks `completeClaim`
- incomplete inventory allows at most `knownInterfaceClaim`
- irreversible information release is not rollback-certified
- global human-feedback residue remains explicit residual risk
- retained live authority blocks authorizing autonomy assessment
- missing seed consumption evidence blocks authorizing autonomy assessment
- `provisionalClaim` and `partialClaim` are not authorizing gate states
- transition certificates must include card evidence and matching expected
  outcome
- modified claim-card hashes block autonomy assessment

Conformance is necessary but not sufficient for high-tier certification. It is a
baseline for local seed, host, and gate behavior.
