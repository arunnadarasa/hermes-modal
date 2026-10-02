#!/usr/bin/env python3
"""Live smoke test for a Modal install: actually runs a function in the
cloud and checks the real result, not just that auth succeeded.

Usage:
    python modal_smoke_test.py [--modal-bin /path/to/modal]

Requires an active Modal profile (modal token set + modal profile
activate already done). Does not print any token/secret values.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_BODY = '''\
import modal

app = modal.App("hermes-skill-smoke-test")

@app.function()
def square(x: int) -> int:
    return x**2

@app.local_entrypoint()
def main():
    result = square.remote(7)
    print(f"SMOKE_TEST_RESULT={result}")
'''

EXPECTED = 49  # 7**2


def find_modal_bin(explicit: str | None) -> str:
    if explicit:
        return explicit
    found = shutil.which("modal")
    if found:
        return found
    # common pip --user install locations as a fallback
    import site
    candidates = [
        Path(site.USER_BASE) / "bin" / "modal",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    print("FAIL: could not locate the 'modal' CLI binary (not on PATH, "
          "not in common fallback locations). Pass --modal-bin explicitly.",
          file=sys.stderr)
    sys.exit(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modal-bin", default=None)
    args = parser.parse_args()

    modal_bin = find_modal_bin(args.modal_bin)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(SCRIPT_BODY)
        script_path = f.name

    try:
        proc = subprocess.run(
            [modal_bin, "run", script_path],
            capture_output=True, text=True, timeout=180,
        )
    finally:
        Path(script_path).unlink(missing_ok=True)

    output = proc.stdout + proc.stderr

    if proc.returncode != 0:
        print("FAIL: modal run exited non-zero")
        print(output[-2000:])
        sys.exit(1)

    m = re.search(r"SMOKE_TEST_RESULT=(\d+)", output)
    if not m:
        print("FAIL: expected result marker not found in output (empty/malformed response)")
        print(output[-2000:])
        sys.exit(1)

    got = int(m.group(1))
    if got != EXPECTED:
        print(f"FAIL: got {got}, expected {EXPECTED} (7**2) — wrong answer, not just an empty one")
        sys.exit(1)

    dashboard_url = None
    url_match = re.search(r"(https://modal\.com/apps/\S+)", output)
    if url_match:
        dashboard_url = url_match.group(1)

    print(f"PASS: remote execution returned {got} (correct)")
    if dashboard_url:
        print(f"Dashboard: {dashboard_url}")
    sys.exit(0)


if __name__ == "__main__":
    main()
