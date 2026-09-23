# AVP Tutor

An algorithm tutor that explains the execution step a student is watching. Runs with **local Ollama** by default, with explicit Gemini, OpenAI, Anthropic, and vLLM options for comparison.

Forked from [huytran088/avp_rag_system](https://github.com/huytran088/avp_rag_system). Original history, grammar, parser, sample algorithms, and optional semantic retrieval are preserved. See [attribution](ATTRIBUTION.md).

The `frontend/` directory is a **temporary test harness only**. Your team's existing/new presentation frontend remains the product UI. Integrate the backend using [the standalone TypeScript client](integrations/tutor-client.ts) and [API contract](docs/integration.md); no React components need to be adopted.

## What works

- An interactive insertion-sort workspace: array bars, saved variables, highlighted AVP, previous/next steps, playback, and custom inputs.
- Explain, hint, prediction-question, and debug modes, with bounded conversation history and explicit before/after execution context.
- Lightweight teaching-note retrieval with source IDs; no embedding downloads at startup.
- A strict integration API for an external visualizer's code, variables, arrays, and recent events.
- AVP syntax diagnostics, separate from semantic checks and runtime correctness.
- 19 **unreviewed draft** training interactions, a 50-case development benchmark, grouped dataset export, and a provider-neutral evaluation runner.
- Retained `/api/generate` and `/api/retrieve` endpoints for upstream integrations. Generation accepts both `query` and legacy `message`.

This repository is a working tutor foundation, **not a trained model or a replacement for the external AVP interpreter**. The demo executes a reference insertion-sort implementation in Python to produce snapshots; arbitrary AVP is never executed. Teaching notes and synthetic targets still need instructor review.

## Run locally

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/getting-started/installation/), Node 22+, and [Ollama](https://docs.ollama.com/quickstart).

```sh
git clone https://github.com/jhunter11/avp-tutor.git
cd avp-tutor
cp .env.example .env
uv sync --frozen
ollama pull qwen3:8b
# Start `ollama serve` if Ollama is not already running.
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd avp-tutor/frontend
npm ci
npm run dev
```

Open http://localhost:5173. The model is configurable; `qwen3:8b` is a starting point, not a claim of best tutoring quality for your hardware. The visualization works without model inference, but the backend must be running.

## Development plan and public teaching data

See the [Waterfall plan](docs/planning/WATERFALL.md) for implemented versus planned capabilities, requirements, phase gates, acceptance criteria, and release scope. Add ideas to [the notes inbox](docs/planning/NOTES.md); accepted changes are tracked in the [change register](docs/planning/CHANGELOG.md).

The [public teaching-data collection](datasets/README.md) includes reproducible, checksum-verified downloads and explicit acquisition limits. It is research material, separate from live RAG and approved AVP training.

## Skills and harness engineering

Edit teaching skills in `harness/skills/`, retrieval policy in `harness/configs/baseline.json`, and grounded context assembly in `tutor/service.py`. Optional consented feedback links ratings to the exact answer/context and harness version. A candidate proposer can scaffold experiments without modifying the active tutor. See [the harness guide](docs/harness.md). Non-use is recorded separately and never automatically interpreted as a bad answer.

## API comparison

For Google AI Studio, set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and `GEMINI_MODEL` in the local `.env`. The Google key is sent only to Google's documented compatibility endpoint. Select a model available to your key. Do not paste keys into chat or commit them.

Alternatively, set `LLM_PROVIDER=openai` with `OPENAI_API_KEY` and `OPENAI_MODEL`, or `LLM_PROVIDER=anthropic` with `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`, in `.env`. Use an exact model ID available in your account. Restart the API after configuration changes. Credentials stay on the backend.

Cloud fallback is **off by default**. Setting `LLM_FALLBACK_PROVIDER` explicitly opts in to sending the same question, code, state, and conversation to that provider when the primary fails. The response identifies the provider/model actually used.

```sh
uv run python -m training.evaluate --limit 5 --output artifacts/local.jsonl
# Change provider/model configuration, then repeat on the same cases:
uv run python -m training.evaluate --limit 5 --output artifacts/api.jsonl
```

Use `--env-file /absolute/path/to/.env` to load credentials from a separate project folder without copying them.

Reports include responses, latency, token usage when available, references, and empty human-review rubric fields. Automated flags are smoke checks, **not accuracy scores**. `--limit 0` runs all 50 cases and makes 50 model calls. The benchmark is development data, not an independent final test set after prompt tuning.

## Integrate your visualizer

Post to `/api/tutor` with `question`, `mode`, `level`, `history`, and `context`. Provide interpreter-generated snapshots; do not ask the model to reconstruct state. See the [integration contract](docs/integration.md), or open `/docs` on the backend for the generated API schema. The workspace also accepts pasted snapshot JSON.

Endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /api/tutor` | Grounded tutoring response and supplied teaching references |
| `POST /api/context/validate` | Validate an integration snapshot without calling a model |
| `POST /api/validate` | Parse AVP; never execute it |
| `GET /api/demo/insertion-sort?values=2,7,9,4` | Deterministic demo snapshots |
| `GET /api/health` | Configuration/liveness status, not proof the model is reachable |
| `POST /api/generate` | Legacy code generation plus syntax diagnostics |
| `POST /api/retrieve` | Legacy function retrieval |

## Training preparation

Start with reviewed **question + code/state + tutor answer** interactions. Logical blocks teach steps; whole algorithms support invariants and complexity. The exporter uses the same prompt builder as inference.

```sh
uv run python -m training.dataset training/seed_examples.jsonl
uv run python -m training.dataset training/seed_examples.jsonl --output artifacts/sft
# The initial export has zero examples: no draft has been marked human-approved.
# To inspect the format only:
uv run python -m training.dataset training/seed_examples.jsonl --output artifacts/draft-preview --include-drafts
```

Read the [training and evaluation guide](docs/training.md) before approving data or training. Conversations are not logged by default or automatically added to training data. Optional feedback capture requires server enablement and per-request consent; see the harness guide.

## Verification

```sh
uv run ruff check .
uv run pytest -q
uv run python -m training.dataset training/benchmark.jsonl
cd frontend
npm ci
npm run build
npx playwright install chromium
npm run test:e2e:ci
```

Browser CI tests intercept model requests. For real-backend integration tests, start the API on port 18080, then run `E2E_LIVE=1 npm run test:e2e -- --project=live`. Live model observations are documented in [verification notes](docs/verification.md).

## Optional semantic search and deployment

Legacy BGE/FAISS retrieval remains available via `uv sync --extra semantic`, `uv run python ingest.py`, and `RETRIEVAL_BACKEND=semantic`. This downloads additional ML dependencies/models and is not needed by the tutor. Invalid source examples are rejected during ingestion.

See [deployment](docs/docker-deploy.md). Deployments are opt-in; this fork does not push to the upstream author's servers or Hugging Face Space. The API has no built-in user authentication: keep the default loopback binding for local use, or put authentication at your application's gateway before public deployment.
