#!/usr/bin/env python3
"""Token guard — fail loudly if a secret pattern ever appears in this repo.
Same pattern as the sibling hermes-*-jev / hermes-amass-mcp guard scripts.
Run before every commit/push.
"""
import re
import sys
from pathlib import Path

PATTERNS = [
    r"ak-[A-Za-z0-9]{15,}",           # Modal token id
    r"as-[A-Za-z0-9]{15,}",           # Modal token secret
    r"(?i)token[_-]?secret['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{15,}",
    r"(?i)token[_-]?id['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{15,}",
    r"(?i)api[_-]?key['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{24,}",
]

BAD = 0
for p in sorted(Path(".").rglob("*")):
    if p.is_file() and p.suffix in (".md", ".yaml", ".yml", ".json", ".py", ".sh", ".txt", ".toml"):
        try:
            t = p.read_text(errors="ignore")
        except Exception:
            continue
        for pat in PATTERNS:
            for m in re.finditer(pat, t):
                print(f"SECRET-LIKE: {p}: {m.group(0)[:40]}")
                BAD += 1
print("GUARD:", "FAIL" if BAD else "CLEAN")
sys.exit(1 if BAD else 0)
