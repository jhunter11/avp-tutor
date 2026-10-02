# AVP Tutor: conservative API cost estimate

Prepared October 1, 2026. Currency: USD. Purpose: faculty discussion and pilot budgeting.

**Recommended planning allowance: $0.03 per learner reply, or $30 per 1,000 replies.**
This allows 20,000 input tokens, 25,000 generated tokens, and one full retry for each reply.
It assumes one tutor call per attempt, uncached input, and standard GPT-6 Luna pricing.
It is a proposed operating envelope, not a measured GPT-6 Luna invoice or a spending guarantee.

## Verified rates and formula

OpenAI lists GPT-6 Luna at $0.10 per million input tokens and $0.50 per million output tokens.
These are standard rates for prompts with no more than 272,000 input tokens.
[Source: official GPT-6 Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna), checked October 1, 2026.

```text
Cost per API call = input tokens / 1,000,000 x $0.10
                  + generated tokens / 1,000,000 x $0.50

Conservative call = 20,000 / 1,000,000 x $0.10
                  + 25,000 / 1,000,000 x $0.50
                  = $0.0020 + $0.0125 = $0.0145

Allow one full retry: 2 x $0.0145 = $0.0290
Round up for planning: $0.03 per learner reply
```

Generated tokens include reasoning and the visible answer. Do not add reasoning tokens a second time.
OpenAI's reasoning guide suggests initially reserving at least 25,000 tokens for reasoning and outputs.
The estimate uses that allowance rather than the much shorter answers observed in the current demo.
[Source: official reasoning guide](https://developers.openai.com/api/docs/guides/reasoning).

## Scenarios, including a full retry

| Scenario | Input tokens per call | Generated tokens per call | Two-call calculation | Planning cost per reply | Cost per 1,000 replies |
|---|---:|---:|---:|---:|---:|
| Short, capped tutor help | 5,000 | 2,000 | $0.003 | $0.005 | $5 |
| Conservative RAG/history/image allowance | 20,000 | 25,000 | $0.029 | $0.03 | $30 |
| Heavy context and reasoning | 100,000 | 25,000 | $0.045 | $0.05 | $50 |

The short scenario requires a smaller output limit and a tested reasoning setting.
It is not the recommended initial budget for untested GPT-6 Luna tutoring.
The conservative scenario's 20,000 inputs include all instructions, code, state, history, retrieved material, and images.
For example, allocate 10,000 tokens to text and provisionally reserve 5,000 for each of two images.
Those image allocations are planning assumptions. They are not measured GPT-6 Luna image counts.

## Example monthly usage

| Monthly learner replies | Example usage | Recommended allowance |
|---:|---|---:|
| 600 | 30 students x 20 replies | $18 |
| 1,000 | A small development or class pilot | $30 |
| 3,000 | 30 students x 100 replies | $90 |
| 10,000 | A larger pilot | $300 |

Each reply can consume two calls under this budget. The table already includes that retry allowance.
Multiply the monthly total by the number of active months for a project estimate.
For a 1,000-reply pilot, a $50 model-API budget adds room beyond the calculated $30 allowance.
This is a proposed budget, not an account spending limit.

## Evidence and limits

The current OpenRouter demo measured about 2,900 input tokens for a short tutoring request.
Ten controlled text and synthetic-image requests reported 54 to 479 output tokens, with no errors or truncation.
A larger test with 80,000 extra background characters reported 17,268 input tokens.
These are measurements of `stealth/space-bunny-alpha`, not GPT-6 Luna.
No paid GPT-6 Luna request ran in this session.
See [the dated token measurements](token-measurements-2026-10-01.md) for inputs, results, and accounting limits.

The image tests added 198 tokens for a 384 x 384 PNG and 1,542 for a 1536 x 768 PNG.
Image tokenization depends on the model, dimensions, and detail settings.
GPT-6 Luna accepts image input, but this test does not establish its image-token usage or image-reading quality.
[Source: official image-input guide](https://developers.openai.com/api/docs/guides/images-vision).

No cache discount, Batch discount, or promotional credit reduces this estimate.
The budget excludes hosting, paid retrieval tools, embedding services, training, taxes, and human review.
V1 retrieval runs locally and uses no model tool calls.
Future multi-call or self-scaffolding workflows need their own call allowance.

The recommendation requires input and output limits and at most one retry.
Those future GPT-6 Luna limits are not configured in the current OpenRouter demo.
The current shared adapter caps generated output at 4,096 tokens, with a local demo setting of 1,600.
The 25,000-token scenario would require a separate configuration change and live evaluation.

Prompts above 272,000 inputs have higher rates: $0.20 input and $0.75 output per million for the whole request.
At 500,000 inputs and 25,000 outputs, two calls cost $0.2375, so reserve $0.25 per reply.
That large-context case is outside the recommended operating envelope.
[Source: official GPT-6 Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna).

Before a paid pilot, verify account access, tutor quality, exact token usage, and rate limits with the selected model.
Keep the current usage counters and record both successful and incomplete responses.
