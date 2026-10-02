# Provider and agent startup pass

User request, October 1, 2026: use OpenRouter now and support other providers through configuration.
Make the demo easy for agents to start on Windows, macOS, and Linux.
The slideshow is outside this task. The parallel V1 demo task owns its standalone UI, routes, interpreter, and focused teaching pack.

## Design

Keep the shared tutor completion interface and existing provider adapters.
Add OpenRouter and a configurable OpenAI-compatible adapter. Select model, endpoint, and key variable through a provider profile.
Store credential variable names in public profiles. Keep credential values in local environment files or inherited environment variables.
Use the free Space Bunny Alpha profile by default. Check zero catalog prices and send zero maximum prices with paid fallback disabled.
Keep the official Gemini compatibility endpoint and its own credential variable. Do not make Gemini calls without a configured key and model.


Provide one Python launcher with doctor, setup, start, stop, and up commands.
Keep platform wrappers thin. Use argument arrays, bounded startup checks, loopback binding, and owned-process identity.
Agents read AGENTS.md and START_HERE.md, then run a documented command. JSON status identifies the URL and configuration readiness.
The demo can open without a model key. Model verification is a separate explicit option.

## Teaching checks

Use the selected first-match question and its actual bounded execution snapshots.
Check question intent, likely misconception, effect, and teaching strategy.
Cover early return, index versus value, duplicates, loop bounds, empty input, absent target, and progress.
Check source limits, skill selection, hint restraint, trace grounding, and configuration hashes without model inference.
Use a few synthetic live OpenRouter requests to check the integrated path. Do not call these a measured teaching-quality score.

## Verification and handoff

Run provider regressions, configuration validation, launcher tests, full backend tests, frontend checks, and the V1 teaching cases.
Add an operating-system CI matrix. Report observed Windows results separately from Linux/macOS CI results.
Publish a branch and PR. Preserve the parallel demo task changes and original commit attribution.
