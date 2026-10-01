"""Fingerprint the public files that affect a running tutor and its teaching pack."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def runtime_version():
    paths = [ROOT / name for name in ["agent_runtime.py", "providers.py", "llm_config.py", "startup_meta.py", "PseudocodeParser.py", "PseudocodeLexer.py"]]
    for directory in ["api", "demo_v1", "harness", "tutor", "knowledge", "config"]:
        paths.extend(path for path in (ROOT / directory).rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".json"})
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        if path.exists():
            digest.update(path.relative_to(ROOT).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()
