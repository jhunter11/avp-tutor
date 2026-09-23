# Plug the tutor into the team's frontend

The product is the backend and its integration contract. `frontend/` is only a temporary testing harness; its styling, layout, and React components need not be adopted.

Copy `tutor-client.ts` and generated `schema.d.ts` together into your UI, or import them from this repository. The client has no runtime dependencies and works with React, Vue, or plain TypeScript. `openapi.json` is also usable by other client generators.

```ts
import { createTutorClient, type ExecutionContext } from './tutor-client';

const tutor = createTutorClient({ baseUrl: 'http://localhost:8000' });
const controller = new AbortController();

// Construct this from your interpreter at the instant the student asks.
const snapshot: ExecutionContext = {
  algorithm: 'insertion_sort',
  language_version: 'your-runtime-version',
  code: 'collection[j + 1] = collection[j]',
  current_line: 1, // one-based within code above
  phase: 'after',
  run_id: 'your-run-id',
  step: 7,
  variables: { j: 2, key: 4 },
  arrays: { collection: [2, 7, 9, 9] },
  recent_events: [{
    kind: 'shift',
    description: 'Copied 9 from index 2 to index 3, overwriting 4; key retains 4.',
    indices: [2, 3],
    details: { source_index: 2, destination_index: 3, copied_value: 9, overwritten_value: 4 }
  }]
};

const reply = await tutor.ask({
  question: 'Did we lose the 4?',
  mode: 'explain',
  level: 'beginner',
  context: snapshot,
  history: []
}, { signal: controller.signal });
// Render reply.answer as text/escaped Markdown, with reply.warnings and sources.
// Associate this reply with snapshot.step, even if playback has since advanced.
```

Use `TutorApiError.status` for 422/429/503 handling. Preserve the question on failure. `retryAfterSeconds` is available if the server returns Retry-After. `AbortController` stops waiting in the UI; an in-flight inference may finish server-side. Supply a `fetcher` wrapper for your existing gateway authentication if needed. Never put provider API keys in the frontend.

The client is typed at compile time; the backend performs runtime request validation. Use `validateContext` while wiring the adapter to test the payload without model calls. See [limits and semantics](../docs/integration.md).

Regenerate types after changing the backend schema:

```sh
uv run python -m scripts.export_openapi
cd frontend
npm run generate:types
```

Backend tests reject a stale committed OpenAPI snapshot. CI regenerates the TypeScript declaration and checks it for drift. Client request/error behavior is covered by `frontend/e2e/client-mocked.spec.ts`.

## Optional learning feedback

After an explicit user opt-in, set `feedback_consent: true` on `ask`. If the server has capture enabled, the reply includes `interaction_id`. Use `client.feedback({interaction_id, rating: 'helpful'})` or a specific problem category. `client.usage({consent:true,event:'dismissed',algorithm:'insertion_sort'})` records aggregate usage separately; dismissal is not a correctness label. See [storage, deletion, and candidate evaluation](../docs/harness.md). The production UI should own the consent and feedback design.
