# AVP Tutor development notes

This fork provides the AI/backend portion of an algorithm visualizer. The team owns the production frontend. `frontend/` is a temporary testing harness, not a proposed replacement UI.

- Read README.md, docs/integration.md, and docs/training.md for current architecture.
- Local Ollama is the default; hosted providers and fallback are explicitly configured.
- Preserve execution facts from the visualizer. Never present syntax validation as runtime verification.
- Keep prompt construction shared between inference and SFT export.
- Do not mark synthetic training targets human-approved.
- Regenerate integrations/openapi.json and schema.d.ts when schemas change. CI checks drift.
- The tutor starts without embeddings; upstream BGE/FAISS retrieval is an optional extra.
- Do not modify generated ANTLR parser files without regenerating them from a verified grammar.
- Add regression tests for bugs; run ruff, pytest, the frontend build, and Playwright before publishing.
- Do not restore the original author's deployment destinations. Deployments are manual.
