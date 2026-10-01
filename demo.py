"""Agent-friendly, standard-library launcher for the local AVP Tutor demo."""

import argparse
import datetime
import getpass
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import webbrowser
from pathlib import Path

from llm_config import ConfigurationError, public_status
from startup_meta import runtime_version

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / ".runtime"
STATE = RUNTIME / "startup.json"


class StartupError(RuntimeError):
    pass


def effective_environment(env_file=None):
    env = dict(os.environ)
    path = Path(env_file or env.get("AVP_DEMO_ENV") or ROOT / ".env").expanduser().resolve()
    if env_file and not path.is_file():
        raise StartupError("The selected environment file does not exist.")
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            match = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
            if not match:
                continue
            value = match[2].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            elif " #" in value:
                value = value.split(" #", 1)[0].rstrip()
            env.setdefault(match[1], value)
        env["AVP_DEMO_ENV"] = str(path)
    return env


def background_options(system=None):
    if (system or platform.system()) == "Windows":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)}
    return {"start_new_session": True}


def doctor(env):
    status = public_status(env)
    ready = sys.version_info >= (3, 12) and bool(shutil.which("uv"))
    return {"ok": ready and "error" not in status, "system": platform.system(),
            "python": platform.python_version(), "python_required": "3.12+", "uv": bool(shutil.which("uv")),
            "demo_files": (ROOT / "demo_v1" / "app.py").is_file(),
            "provider": status, "model_reachability": "not checked", "root": str(ROOT)}


def setup(env):
    if sys.version_info < (3, 12):
        raise StartupError("Use Python 3.12 or newer.")
    uv = shutil.which("uv")
    if not uv:
        raise StartupError("Install uv from its official source, then retry. See START_HERE.md.")
    completed = subprocess.run([uv, "sync", "--frozen"], cwd=ROOT, env=env, check=False)
    if completed.returncode:
        raise StartupError(f"Dependency setup failed with exit code {completed.returncode}.")


def read_json_url(url):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.load(response)


def saved_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def owned_identity(state):
    if not isinstance(state, dict):
        return None
    port = state.get("port")
    if type(port) is not int or not 1024 <= port <= 65535:
        return None
    try:
        live = read_json_url(f"http://127.0.0.1:{port}/__agent/status")
    except (OSError, ValueError, urllib.error.URLError):
        return None
    if (live.get("application") == "avp-tutor" and live.get("instance") == state.get("instance")
            and live.get("pid") == state.get("pid") and Path(live.get("root", "")).resolve() == ROOT):
        return live
    return None


def stop():
    state = saved_state()
    live = owned_identity(state)
    if not live:
        if state:
            raise StartupError("The saved process identity does not match. No process was stopped.")
        return {"ok": True, "running": False}
    os.kill(live["pid"], signal.SIGTERM)
    for _ in range(50):
        if not owned_identity(state):
            STATE.unlink(missing_ok=True)
            return {"ok": True, "running": False, "stopped_pid": live["pid"]}
        time.sleep(0.1)
    raise StartupError("The owned server did not stop within five seconds.")


def start(env, port=8771, app="demo_v1.app:app", open_browser=False):
    if not 1024 <= port <= 65535:
        raise StartupError("Choose a port from 1024 through 65535.")
    status = public_status(env)
    if "error" in status:
        raise StartupError(status["error"])
    if app == "demo_v1.app:app" and not (ROOT / "demo_v1" / "app.py").is_file():
        raise StartupError("This checkout does not contain the V1 demo. Use the complete demo branch.")
    previous = saved_state()
    live = owned_identity(previous)
    if live:
        if (previous["port"] != port or live["app"] != app
                or live["provider"] != status or live.get("runtime_version") != runtime_version()):
            raise StartupError("This checkout already runs with another configuration or older code. Run restart to load the requested version.")
        result = {**previous, "ok": True, "running": True, "reused": True, "provider": live["provider"]}
        if open_browser:
            webbrowser.open(result["url"])
        return result
    with socket.socket() as check:
        try:
            check.bind(("127.0.0.1", port))
        except OSError:
            raise StartupError("The selected port is occupied. Choose --port with another number.") from None
    uv = shutil.which("uv")
    if not uv:
        raise StartupError("uv is missing. Run doctor and read START_HERE.md.")
    RUNTIME.mkdir(exist_ok=True)
    instance = uuid.uuid4().hex
    child_env = {**env, "AVP_STARTUP_APP": app, "AVP_STARTUP_INSTANCE": instance}
    command = [uv, "run", "--frozen", "uvicorn", "agent_runtime:app", "--host", "127.0.0.1", "--port", str(port)]
    with (RUNTIME / "backend.log").open("ab") as log:
        process = subprocess.Popen(command, cwd=ROOT, env=child_env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log, **background_options())
    url = f"http://127.0.0.1:{port}" + ("/" if app == "demo_v1.app:app" else "/docs")
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise StartupError("The server exited during startup. Inspect .runtime/backend.log.")
        try:
            identity = read_json_url(f"http://127.0.0.1:{port}/__agent/status")
            if identity.get("instance") != instance:
                raise StartupError("The port answered from another process. No existing process was stopped.")
            with urllib.request.urlopen(url, timeout=3) as page:
                if page.status != 200:
                    continue
            state = {"instance": instance, "pid": identity["pid"], "port": port, "url": url,
                     "app": app, "root": str(ROOT), "provider": identity["provider"],
                     "runtime_version": identity["runtime_version"],
                     "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
            STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
            if open_browser:
                webbrowser.open(url)
            return {**state, "ok": True, "running": True, "reused": False}
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(0.25)
    process.terminate()
    raise StartupError("The server did not become ready within the startup limit.")


def configure_key(env):
    selected = public_status(env)
    variable = selected.get("credential_variable")
    if not variable:
        raise StartupError("This profile has no required credential variable.")
    value = getpass.getpass(f"Enter {variable} locally (hidden): ").strip()
    if not value or any(c in value for c in "\r\n\"'"):
        raise StartupError("Use a nonempty single-line API key.")
    target = Path(env.get("AVP_DEMO_ENV") or ROOT / ".env")
    lines = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    lines = [line for line in lines if not re.match(rf"\s*(?:export\s+)?{re.escape(variable)}\s*=", line)]
    target.write_text("\n".join([*lines, f'{variable}="{value}"']) + "\n", encoding="utf-8")
    if os.name != "nt":
        target.chmod(0o600)
    return {"ok": True, "credential_variable": variable, "saved_to": str(target), "value_printed": False}


def verify_model(env):
    status = public_status(env)
    if not status.get("configured"):
        raise StartupError("Configure the selected provider key and model before verification.")
    # One synthetic public prompt. No learner history, source repository, or private data.
    command = [shutil.which("uv") or "uv", "run", "--frozen", "python", "-c",
               "from providers import call_chat; import json; r=call_chat([{'role':'user','content':'In one sentence, why should a linear search check every item before returning not found?'}]); print(json.dumps({'ok':True,'provider':r.provider,'model':r.model,'answer':r.answer,'truncated':r.truncated}))"]
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=200)
    if completed.returncode:
        raise StartupError("Model verification failed. Check the selected key, model, availability, and quota.")
    return json.loads(completed.stdout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "setup", "start", "stop", "restart", "up", "configure-key", "verify-model"], nargs="?", default="up")
    parser.add_argument("--provider", help="Configured profile name")
    parser.add_argument("--model", help="Exact model ID for the selected provider")
    parser.add_argument("--env-file", type=Path, help="Existing local environment file")
    parser.add_argument("--port", type=int, default=8771)
    parser.add_argument("--app", choices=["demo_v1.app:app", "api.main:app"], default="demo_v1.app:app")
    parser.add_argument("--open", action="store_true", help="Open the browser after readiness succeeds")
    parser.add_argument("--json", action="store_true", help="Machine-readable status")
    args = parser.parse_args(argv)
    try:
        env = effective_environment(args.env_file)
        if args.provider:
            env["LLM_PROVIDER"] = args.provider
        if args.model:
            env[env.get("LLM_PROVIDER", "openrouter").upper().replace("-", "_") + "_MODEL"] = args.model
        if args.command == "doctor":
            result = doctor(env)
        elif args.command == "setup":
            setup(env)
            result = doctor(env)
        elif args.command == "stop":
            result = stop()
        elif args.command == "configure-key":
            result = configure_key(env)
        elif args.command == "verify-model":
            result = verify_model(env)
        else:
            if args.command == "up":
                setup(env)
                current = owned_identity(saved_state())
                if current:
                    if (current["provider"] != public_status(env) or current.get("runtime_version") != runtime_version()
                            or current["app"] != args.app or saved_state()["port"] != args.port):
                        stop()
            elif args.command == "restart":
                if saved_state():
                    stop()
            result = start(env, args.port, args.app, args.open)
        print(json.dumps(result, indent=2) if args.json else json.dumps(result))
        return 0 if result.get("ok") else 1
    except (StartupError, ConfigurationError, subprocess.TimeoutExpired, OSError) as error:
        message = "The operation exceeded its time limit." if isinstance(error, subprocess.TimeoutExpired) else str(error)
        if isinstance(error, OSError):
            message = "A local file or process operation failed. Check prerequisites and directory permissions."
        print(json.dumps({"ok": False, "error": message}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
