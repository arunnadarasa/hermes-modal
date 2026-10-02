# hermes-modal

Hermes Agent skill for wiring [Modal](https://modal.com) — serverless
Python cloud compute (GPU inference, batch jobs, sandboxes, scheduled
functions) — into Hermes as a CLI invoked via `terminal`. Modal is not an
MCP server; there's no `mcp_modal_*` tool namespace.

Documentation source: [modal.com/llms-full.txt](https://modal.com/llms-full.txt)

## What Modal provides

- Serverless Python functions (`@app.function()`), scale-to-zero, no YAML
- GPU inference (`gpu="h100"`, `gpu="H200:8"`) with sub-second cold starts
- Sandboxes for isolated/untrusted code execution
- Scheduled jobs and massively parallel batch processing
- GPU-backed collaborative notebooks

## Layout

```
skills/hermes-modal/SKILL.md
skills/hermes-modal/scripts/modal_smoke_test.py
```

## Install + auth

```bash
pip3 install modal
which modal   # confirm it's on PATH; use the full path if not

modal token set --token-id ak-... --token-secret as-... --profile=<name>
modal profile activate <name>
modal token info   # verify — never `cat ~/.modal.toml` (plaintext secret)
```

Full detail — including the PATH gotcha in non-interactive tool runners,
the env-var-overrides-profile trap, and why you should never read
`~/.modal.toml` directly — is in `skills/hermes-modal/SKILL.md`.

## Verification

A real remote-execution smoke test, not just an auth check:

```bash
python skills/hermes-modal/scripts/modal_smoke_test.py
```

Runs an actual `@app.function()` on Modal's cloud (`square(7)`) and asserts
the correct numeric result came back, printing the live dashboard URL.
Live run (2026-10-02): **PASS, 49 (7**2), dashboard confirmed.**

## Security

No token values belong in this repository. The smoke test never prints a
token/secret and expects auth to already be configured via `modal token
set`. Run `scripts/guard_secrets.py` before every push. Never paste a
credential into a command line, issue, commit, or chat — and never `cat`
`~/.modal.toml` in a shared/logged context, since it stores the token
secret in plaintext.
