"""Add a private-process identity to the selected local ASGI app."""

import importlib
import os
from pathlib import Path

from llm_config import public_status
from startup_meta import runtime_version

LOADED_VERSION = runtime_version()

target = os.environ.get("AVP_STARTUP_APP", "demo_v1.app:app")
if target not in {"demo_v1.app:app", "api.main:app"}:
    raise RuntimeError("Select the V1 demo or the integration API as the startup app.")
module, attribute = target.split(":")
app = getattr(importlib.import_module(module), attribute)


@app.get("/__agent/status", include_in_schema=False)
def startup_status():
    return {"application": "avp-tutor", "instance": os.environ.get("AVP_STARTUP_INSTANCE", ""),
            "pid": os.getpid(), "root": str(Path(__file__).resolve().parent),
            "app": target, "provider": public_status(), "runtime_version": LOADED_VERSION}


# The standalone document mounts '/' last. Put readiness before that catch-all mount.
agent_route = next(route for route in app.router.routes if getattr(route, "endpoint", None) is startup_status)
app.router.routes.remove(agent_route)
app.router.routes.insert(0, agent_route)
