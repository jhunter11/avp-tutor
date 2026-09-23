import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def client_ip(request: Request) -> str:
    # Trust only explicitly configured direct proxy addresses. Never trust headers
    # from arbitrary clients when the server is exposed directly.
    peer = get_remote_address(request)
    trusted = {
        ip.strip()
        for ip in os.environ.get("TRUSTED_PROXY_IPS", "").split(",")
        if ip.strip()
    }
    if peer in trusted:
        value = request.headers.get("x-real-ip", "").strip()
        if value:
            return value
    return peer


limiter = Limiter(key_func=client_ip)
