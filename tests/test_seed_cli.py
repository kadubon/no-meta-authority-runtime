from __future__ import annotations

import subprocess
import sys


def test_seed_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "no_meta_authority_runtime.seed.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "no-meta-seed" in result.stdout
