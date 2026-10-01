# Start the AVP Tutor demo

Read this file first. The standalone demo needs Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Node and a local model are optional. Startup does not download embeddings.

## Run

Windows:

```powershell
python demo.py up --open --json
```

macOS or Linux:

```sh
python3 demo.py up --open --json
```

The launcher installs locked dependencies, starts the server, checks the page, and opens `http://127.0.0.1:8771/`.
Windows also has `Start Demo.cmd`. macOS has `Start Demo.command`. Linux has `./start-demo.sh`.

The default provider is OpenRouter with `stealth/space-bunny-alpha`.
The launcher uses an inherited `OPENROUTER_API_KEY` or a local `.env` file.
Without a key, code execution and trace controls work. Tutor messages require a configured provider.

Enter a key locally through a hidden terminal prompt:

```sh
python demo.py configure-key --provider openrouter
python demo.py restart --open --json
```

Use `python3` on macOS or Linux. Never paste a key into agent chat or commit it.
An external credentials file works with `--env-file /absolute/path/to/.env`.
Process variables override values from that file.

## Agent instructions

Give an agent this request after cloning the repository:

> Read START_HERE.md and AGENTS.md. Run doctor, then bring up the standalone demo and open its reported URL. Use the existing local provider configuration. Report whether the page works and whether model inference was tested. Do not print credentials.

Useful commands:

```sh
python demo.py doctor --json
python demo.py up --json
python demo.py verify-model --json
python demo.py stop --json
```

`doctor` checks configuration and prerequisites. It does not call a model.
`verify-model` sends one synthetic question to the selected provider.
The launcher reuses a matching server. `up` reloads changed code or public provider settings.
Use `restart` after key changes. Use `--port 8772` if another application owns port 8771.
The launcher stops only the server whose identity matches this checkout.

## Present the question

The question asks for the first matching array index, or minus one when the target is absent.
Run the sample flawed code, inspect the trace, and ask for a hint.
The flawed program passes four of six fixed cases. The corrected program passes six.
Use Explain, Debug, or Predict to change the teaching method.
The page shows source cards and the exact execution context attached to an answer.

The demo has four fixed teaching skills and seven confusion cards.
It retrieves short local facts and teaching methods without a vector database.
See [the teaching checks](docs/demo-teaching-checks.md) and [provider configuration](docs/providers.md).
See [the V1 guide](docs/demo-v1.md) for execution limits and learner-note controls.

The original integration API is separate. Start it with `--app api.main:app` when needed.
The `frontend/` React application remains an optional test harness.
