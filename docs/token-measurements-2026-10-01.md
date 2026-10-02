# AVP Tutor token measurements

Date: October 1, 2026. Actor: Codex. Model: OpenRouter `stealth/space-bunny-alpha`.

Ten controlled synthetic requests returned answers without provider errors or truncation.
The test used the actual V1 prompt builder, four fixed skills, and the existing free-only provider policy.
The measured modes were Hint, Explain, and Debug. Earlier teaching checks covered Predict.
Learner-note recall was off.
These measurements do not establish GPT-6 Luna token counts, teaching quality, or provider reliability.

## Provider-reported usage

| Scenario | Input tokens | Total output tokens | Seconds |
|---|---:|---:|---:|
| Current hint | 2,936 | 342 | 6.672 |
| Current explanation | 2,864 | 54 | 3.260 |
| Current debugging | 2,859 | 218 | 4.996 |
| Eight history turns, 9,600 characters | 4,692 | 201 | 2.888 |
| Add 20,000 background characters | 6,525 | 479 | 8.488 |
| Add 80,000 background characters | 17,268 | 358 | 4.519 |
| Text-only image control | 2,936 | 219 | 3.665 |
| Add one 384 x 384 image | 3,134 | 210 | 5.955 |
| Add one 1536 x 768 image | 4,478 | 362 | 6.486 |
| Add four 384 x 384 images | 3,728 | 374 | 6.972 |

The image requests used synthetic array-bar PNGs with default image detail.
The four-image case repeated the same image four times.
Relative to the matching text control, the increments were 198, 1,542, and 792 input tokens.
These are observed request increments, including media framing. They are not universal image-token formulas.
The requests establish that this route accepted images. They do not test visual reasoning or OCR quality.
The product demo still accepts text only. The image tests ran through the measurement script.

The 20,000- and 80,000-character cases used repeated, project-authored background examples.
They did not load a real teaching corpus or exceed the model's advertised context window.
The largest measured input was 17,268 tokens. The advertised one-million-token limit was not tested.
History stayed within V1's eight-turn and 10,000-character bounds.
The larger background probes represent a future harness, outside the current request schema.

## Reasoning and caching

Output totals do not equal the visible answer length.
A diagnostic returned 390 output tokens, 124 answer characters, and 1,505 separate reasoning characters.
The provider nevertheless reported zero reasoning tokens.
The final adapter records reasoning length without retaining its text and marks that split unavailable.
The demo displays reported input/output totals and cached input counts when available.
Missing counts remain unknown.
The published guard also marks a split unavailable when reasoning exceeds total output or the total is missing.

The original ten receipts contain a derived `non_reasoning_output_tokens` field.
Do not interpret that field as visible answer tokens.
The diagnostic exposed an accounting inconsistency after those receipts were saved.
`accounting-correction.json` preserves the correction, and the final runner avoids that derived count when the split is inconsistent.

Input totals include cached tokens. Adding cached tokens to the input total would count them twice.
Repeated prompts reported substantial caching, but the cost proposal assumes no cache discount.
[OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting) documents the returned usage fields.

## Context growth

The baseline has about 11,500 text characters and 2,900 input tokens.
System instructions occupy 5,150 characters.
Facts, method cards, execution context, test summaries, and the teaching plan supply most of the remaining text.
The learner's question is a small part of the request.

Adding documents to the retrieval index does not send those documents automatically.
V1 sends at most three fact sections and two method cards.
Prompt size grows when selected sections get longer, retrieval limits rise, or more history and media enter the request.
The measured prose additions averaged about 5.6 characters per added token.
Code and JSON can have a different ratio. Character estimates remain rough.

## Reproduce

The default command makes no model calls:

```sh
uv run python -m scripts.measure_demo_tokens
```

A live run makes at most ten calls through the configured provider:

```sh
uv run python -m scripts.measure_demo_tokens --live --output artifacts/token-review/measurements.jsonl
# Select one case instead:
uv run python -m scripts.measure_demo_tokens --live --case one-image-384
```

`--live` sends requests to the configured provider. A future paid-provider configuration can incur charges.
The recorded measurements used free-only OpenRouter. The offline command sends no model requests.

The script appends dated receipts. Each receipt records configuration names, prompt hashes, image dimensions, byte counts, and image hashes.
It does not save credentials, image base64, or reasoning text.
The original local receipts are in `artifacts/token-review-20261001/`, which Git ignores.

The full backend suite exited 0 with 154 passing tests.
Ruff and JavaScript syntax checks exited 0.
The later count-validity guard passed 156 backend tests and the 14 original frontend browser tests.
Its offline runner check made no model calls.
The final instrumentation recheck reported 2,936 input tokens and 275 output tokens, with an unavailable reasoning split.
The live browser showed 2,936 input tokens and 319 output tokens, with the same split warning.

See [the conservative API budget](avp-api-budget-2026-10-01.md) for the teacher estimate.
