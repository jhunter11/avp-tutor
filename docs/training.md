# Post-training and evaluation

## Train tutoring behavior, not raw code memorization

The unit is a request containing a student's question, relevant code block or complete algorithm, execution state, recent events, and optional conversation, paired with a reviewed tutor response. Whole-function context supports correctness and complexity questions; complete logical blocks support local explanations. Avoid arbitrary fixed-line slicing.

Start with supervised fine-tuning of an instruction-tuned local model. Keep live state and teaching references at inference time. Fine-tuning does not replace those inputs. First establish a prompted baseline on the same deployment hardware. Use LoRA/QLoRA only after selecting a compatible base model, trainer, hardware, and export path; no training job or trained adapter is included or claimed here. Ollama serves the resulting supported model/adapter; it is not this project's training engine. Follow [Ollama's import documentation](https://docs.ollama.com/import) for the selected architecture.

## Included data and review

`seed_examples.jsonl` has 19 synthetic drafts. `benchmark.jsonl` has 50 development cases (36 trace-grounded interactions and 14 conceptual questions). They are small development fixtures, not a complete curriculum or independent evidence of generalization. `scripts/build_seed_data.py` rebuilds these deterministically.

Each record contains:
- `id`, `algorithm`, `program_id`, and `trace_id` for provenance and grouping;
- the exact production `request`, target `answer`, and `expected_facts`;
- `provenance`, `review_status`, and `reviewed_by`.

An instructor should check every factual claim against the trace/runtime, verify the language reference, and judge whether hints preserve useful student work. Only after that review set `review_status=approved` and an actual reviewer identity in `reviewed_by`. Do not label an automated review as human approval. Approved records require a reviewer. Collect real student sessions only with consent and remove identifying material; the app does not silently collect them.

The exporter rejects malformed examples and duplicate IDs/interactions, excludes drafts by default, and writes ordinary chat-message JSONL with the same prompt and retrieval format used at runtime. `--include-drafts` is for inspecting the pipeline, not evidence the targets are ready to train on. The export manifest identifies draft inclusion and prompt/knowledge versions.

## Leakage prevention

Partitions are connected groups: all examples sharing an algorithm, program ID, trace ID, or identical normalized nonempty code remain together. Algorithm-level grouping intentionally tests transfer. Fewer than three independent groups cannot make a meaningful train/validation/test split; the manifest explicitly reports empty partitions. Keep the manifest with the training run. Near-duplicate implementations with renamed identifiers still require human review.

The included development benchmark overlaps concepts and templates with seeds. Never report it as a held-out final test after tuning prompts or training on the seeds. Create a separate instructor-authored test set using new implementations, questions, learners, and traces before making performance claims.

## Comparison and scoring

Run the same cases with the same prompt/knowledge versions against the untuned local model, hosted baseline, and fine-tuned local model. Record hardware, model digest/quantization, token usage, latency, and settings. Freeze the final test set before training.

Rate each answer 0–2 on:
1. State accuracy: correct values, phase, line, and observed event.
2. Algorithm correctness: invariant, complexity, preconditions, and edge cases.
3. Teaching usefulness: addresses the actual question; hints do not spoil; prediction mode asks a useful question.

Flag fabricated AVP constructs, claims of execution without evidence, unsupported citations, and confidently resolving contradictory context. Include no-context questions, unsupported features, adversarial comments, misconceptions, follow-ups, and multiple valid implementations. A teacher API can draft examples; its answers still require checking. The evaluator emits **unfilled** human rubric fields and limited mechanical flags rather than inventing correctness scores.

Useful references: [NExT execution-trace research](https://arxiv.org/abs/2404.14662), [training data should match production inputs](https://help.openai.com/en/articles/6811186). NExT studies code repair, not a demonstrated tutoring outcome for this project.
