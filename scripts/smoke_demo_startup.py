"""Cross-platform model-free launcher round trip, suitable for CI."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = dict(os.environ)
    for name in list(env):
        if name.endswith("API_KEY") or name in {"AVP_DEMO_ENV", "LLM_FALLBACK_PROVIDER", "LLM_PROVIDERS_FILE"}:
            env.pop(name)
    env.update(LLM_PROVIDER="openrouter", OPENROUTER_MODEL="stealth/space-bunny-alpha")
    with socket.socket() as candidate:
        candidate.bind(("127.0.0.1", 0))
        port = candidate.getsockname()[1]
    with tempfile.TemporaryDirectory() as folder:
        blank = Path(folder) / ".env"
        blank.write_text("", encoding="utf-8")

        def run(command):
            result = subprocess.run(
                [sys.executable, "demo.py", command, "--port", str(port), "--env-file", str(blank), "--json"],
                cwd=ROOT, env=env, capture_output=True, text=True, timeout=60,
            )
            if result.returncode:
                raise AssertionError(f"Launcher {command} failed: {result.stdout}")
            return json.loads(result.stdout)

        # Run only in an isolated checkout without an existing launcher-owned server.
        if (ROOT / ".runtime" / "startup.json").exists():
            raise RuntimeError("Use an isolated checkout without an existing startup record.")
        started = run("start")
        try:
            assert started["running"] and not started["provider"]["configured"]
            with urllib.request.urlopen(started["url"], timeout=5) as page:
                assert page.status == 200
            with urllib.request.urlopen(started["url"] + "demo/api/status", timeout=5) as response:
                assert not json.load(response)["configured"]
            repeated = run("start")
            assert repeated["reused"] and repeated["pid"] == started["pid"]
        finally:
            stopped = run("stop")
            assert not stopped["running"]
    print(json.dumps({"ok": True, "checks": ["no-key-page", "reuse", "owned-stop"], "model_calls": 0}))


if __name__ == "__main__":
    main()
