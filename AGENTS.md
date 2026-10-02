# Agent entry point

Read START_HERE.md first. It contains the complete standalone demo startup procedure.
Use `python demo.py doctor --json`, then `python demo.py up --json`.
Open the reported URL only after startup succeeds.
Use `python3` on macOS and Linux.

Provider profiles live in config/providers.json. Credentials stay in process variables or an ignored local .env file.
Use the hidden `configure-key` prompt when a user needs to enter a key.
Do not print credentials or include them in artifacts.
OpenRouter is the default. Gemini, OpenAI, Anthropic, Ollama, and compatible servers have separate profiles.
See docs/providers.md before changing a provider.

Demo execution uses a bounded interpreter. Preserve its observed results in tutor context.
Treat confusion cards as hypotheses. Do not claim that a keyword match proves a student misunderstanding.

Keep learner notes local and optional. Do not export operator memory into this repository.

For implementation, read CLAUDE.md and only the files relevant to the change.
Run Ruff and pytest. Run the original frontend build and browser tests before publication.
Run scripts/smoke_demo_startup.py for launcher changes. It makes no model calls.
Use a branch and pull request. Preserve unrelated changes and the configured Git identity.
