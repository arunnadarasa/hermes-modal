---
name: hermes-modal
description: "Wire Modal (serverless GPU/CPU cloud compute) into Hermes."
version: 1.0.0
---

# Hermes Modal

Wires [Modal](https://modal.com) — a serverless Python cloud-compute
platform (GPU inference, batch jobs, sandboxes, scheduled functions) — into
Hermes as a CLI the agent can call via `terminal`. Modal is NOT an MCP
server; there's no `mcp_modal_*` tool namespace. It's a `pip`-installed
Python package + CLI authenticated via a profile token, invoked directly
(`modal run ...`, `modal deploy ...`). Verified live 2026-10-02 against
`api.modal.com` (client 1.6.0).

## 1. What Modal provides

- **Functions**: decorate a Python function with `@app.function()`; Modal
  runs it in an on-demand container (CPU/GPU/memory configured in code, no
  YAML) and scales to zero when idle.
- **GPU inference**: `@app.function(gpu="h100")` or `gpu="H200:8"` for
  multi-GPU — sub-second cold starts advertised for serving open-weight or
  custom models.
- **Sandboxes**: isolated, secure containers for executing
  untrusted/AI-generated code.
- **Scheduled jobs / batch processing**: fan out massively parallel work
  across containers.
- **Notebooks**: GPU-backed, collaborative.
- $30/month of free credits on signup; a GPU function requires a valid
  payment method on file regardless of credit balance.

## 2. Install

```bash
pip3 install modal
```

The `modal` CLI script lands in the user Python scripts directory (e.g.
`~/Library/Python/3.14/bin` on macOS with the system `python3`), which is
**not always on PATH by default** in a plain shell, and is NEVER on PATH
inside a non-interactive tool runner that doesn't source your shell rc file
(confirmed: Hermes's own `terminal` tool does not source `.zshrc`/`.bashrc`
— every `modal` invocation from an agent session needs either a full path
or an explicit `export PATH=...` prefix, even if the user's real terminal
already resolves `modal` fine via their shell rc).

- **User-facing shells**: most dotfiles already glob-cover version-specific
  Python bin dirs (e.g. `export PATH="$HOME/Library/Python/3.*/bin:$PATH"`
  in `.zshrc`) — check before assuming a PATH fix is needed; it may already
  be handled.
- **Agent/tool-runner shells**: always verify with `which modal` after
  install; if empty, use the full path reported by the pip install warning
  (`WARNING: The script modal is installed in '<path>' which is not on
  PATH`) or prefix every command with
  `export PATH="$PATH:<that dir>"`.

## 3. Auth — token + named profile

Modal's docs push `modal setup` (interactive browser OAuth), but a
pre-issued token pair (`token-id` / `token-secret`, from
modal.com → Settings → Tokens) wires non-interactively and supports naming
a profile — useful when more than one Modal workspace/account is in play:

```bash
modal token set --token-id ak-... --token-secret as-... --profile=<profile-name>
modal profile activate <profile-name>
```

- `modal token set` **verifies the token live** against
  `api.modal.com`/`api.modal2.com` before writing it — a bad token-id/secret
  pair fails immediately with a clear error, not a silent write.
- Token is written to `~/.modal.toml` as a TOML section named after the
  profile, in PLAINTEXT (`token_id` + `token_secret` both in cleartext, no
  encryption at rest). Treat this file exactly like a credentials file —
  never `cat` it in a shared/logged context (see Pitfalls).
- `modal profile activate <name>` sets `active = true` for that profile's
  TOML section; `modal profile current` and `modal token info` both confirm
  which profile/workspace is actually in effect.
- **Env-var override trap**: if `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` are
  set as environment variables (e.g. sourced from a `.env` file before
  running `modal`), they **silently override** the active `~/.modal.toml`
  profile — `modal token set` prints this warning explicitly at write time.
  If you intend the named profile to be authoritative, do not also export
  these env vars in any shell init path or `.env` the agent might source
  before invoking `modal`. Decide one source of truth and remove the other.

### Verify

```bash
modal token info     # confirms Token/Name/Workspace/User/Created-at for the active profile
modal profile current
```

## 4. Smoke test (real remote execution, not just auth)

Auth succeeding is not the same as compute working. Run an actual function
end-to-end:

```bash
python skills/hermes-modal/scripts/modal_smoke_test.py
```

Writes a tiny `@app.function()` that computes `x**2`, calls
`modal run <script>`, and asserts the printed result contains the correct
square — a genuine round-trip to Modal's cloud, not a local no-op. A
successful run also prints a `https://modal.com/apps/<workspace>/...` URL
you can open to see the real App/Function/container in the dashboard.

## Pitfalls (one line each)

- **`cat ~/.modal.toml` (or any command that echoes the file) prints the
  plaintext `token_secret` into terminal/chat output** — same exposure
  class as any other credential leak; if this happens, rotate the token at
  modal.com → Settings → Tokens and re-run `modal token set` with the new
  pair. Use `modal token info` (which truncates the token ID and never
  shows the secret) to verify instead of reading the TOML file directly.
- The `modal` CLI script's install location is not guaranteed to be on
  PATH — check with `which modal` right after install, every time, on a
  fresh machine/tool-runner; don't assume the prior session's PATH state
  carries over.
- `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` env vars silently beat the
  `~/.modal.toml` active profile — if you're debugging "why did
  `modal profile activate` not seem to take effect," check `env | grep
  MODAL_TOKEN` first.
- A GPU function (`gpu="h100"` etc.) requires a valid payment method on
  Modal regardless of free-credit balance — a CPU-only function
  (`@app.function()` with no `gpu=`) is the right smoke-test shape to avoid
  surprising a billing gate.
- Modal is a plain CLI/SDK, not an MCP server — there is no `hermes mcp
  add` step and no `mcp_modal_*` tool namespace; the agent calls it via
  `terminal`, same as `git` or `gh`.
- Key values never in repo/skill/commit — env-var/token names only; run the
  guard before push.
