# Deployment

For local development, use the README commands with the API bound to loopback. No inherited upstream destination is used automatically.

## Docker

```sh
cp .env.example .env
# Start Ollama on the host and pull the configured model.
docker compose up --build
```

Open http://localhost:8000. `Dockerfile.full` builds the frontend and serves it with the API. Compose overrides `OLLAMA_BASE_URL` to `http://host.docker.internal:11434`; the model server must be reachable from the container. On Linux the host-gateway entry resolves the host, but a loopback-only Ollama server may require a carefully configured host binding/firewall. Do not expose Ollama publicly. `Dockerfile` builds the backend only.

The image includes the parser, lightweight retrieval corpus, and tutoring notes. It does not download embedding weights or bundle an Ollama model. The image health check tests API liveness, not model availability. Docker requires an available Docker daemon and is separate from the Python/frontend release checks.

## Separate frontend

Configure `VITE_API_BASE_URL` at build time and add the frontend's exact origin to backend `CORS_ORIGINS`. GitHub Pages cannot host the Python API or provide access to a user's private localhost model server. Use a reachable HTTPS backend. The Pages workflow is manual and requires that backend variable; it does not run on every push.

## Public hosting

The API has no application login or tenant layer. Put it behind your existing visualizer authentication/gateway before allowing public traffic. Set request/concurrency budgets there. Only configure `TRUSTED_PROXY_IPS` for direct proxies that overwrite X-Real-IP. CORS is not authentication. API keys must remain server-side. Hosted fallback is explicit because it changes where student code/state is sent.

There is no auto-sync or force-push workflow targeting the upstream author's Hugging Face Space.
