# AVP Tutor development notes

This fork supplies the AI/backend portion of an algorithm visualizer. The team owns the production frontend.
`frontend/` is a temporary testing harness.

- Read START_HERE.md and AGENTS.md first for the standalone demo.
- Read docs/integration.md and docs/training.md only for integration or training work.
- OpenRouter is the default. Public profiles select other providers. Cross-provider fallback needs explicit configuration.
- Preserve execution facts from the visualizer. Never present syntax validation as runtime verification.
- Keep prompt construction shared between model calls and SFT export.
- Do not mark synthetic training targets human-approved.
- Regenerate integrations/openapi.json and schema.d.ts when schemas change. CI checks drift.
- The tutor starts without embeddings. Upstream BGE/FAISS retrieval is an optional extra.
- Do not modify generated ANTLR parser files without regenerating them from a verified grammar.
- Add regression tests for bugs. Run ruff, pytest, the frontend build, and Playwright before publishing.
- Do not restore the original author's deployment destinations. Deployments are manual.
