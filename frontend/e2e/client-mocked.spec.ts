import { test, expect } from "@playwright/test";
import {
  createTutorClient,
  TutorApiError,
} from "../../integrations/tutor-client";

test("client preserves execution context and caller cancellation", async () => {
  let captured: RequestInit | undefined;
  let endpoint = "";
  const controller = new AbortController();
  const client = createTutorClient({
    baseUrl: "https://example.test/",
    fetcher: async (url, init) => {
      endpoint = String(url);
      captured = init;
      return new Response(JSON.stringify({ answer: "saved" }), { status: 200 });
    },
  });
  await client.ask(
    {
      question: "why",
      mode: "hint",
      level: "beginner",
      context: {
        algorithm: "insertion_sort",
        code: "x = 1",
        language_version: "avp-v1",
        phase: "after",
        run_id: "run1",
        current_line: 1,
        variables: { key: 4 },
      },
    },
    { signal: controller.signal },
  );
  expect(endpoint).toBe("https://example.test/api/tutor");
  expect(captured?.signal).toBe(controller.signal);
  expect(JSON.parse(String(captured?.body)).context.variables.key).toBe(4);
});

test("client returns structured validation failures", async () => {
  const client = createTutorClient({
    fetcher: async () =>
      new Response(
        JSON.stringify({
          detail: [{ loc: ["body", "question"], msg: "Too long" }],
        }),
        { status: 422 },
      ),
  });
  try {
    await client.ask({ question: "why", mode: "explain", level: "beginner" });
    throw new Error("Expected failure");
  } catch (error) {
    expect(error).toBeInstanceOf(TutorApiError);
    expect((error as TutorApiError).status).toBe(422);
    expect((error as Error).message).toContain("Too long");
  }
});

test("client preserves retry-after on rate limiting", async () => {
  const client = createTutorClient({
    fetcher: async () =>
      new Response("Rate limit exceeded", {
        status: 429,
        headers: { "Retry-After": "12" },
      }),
  });
  await expect(
    client.ask({ question: "why", mode: "explain", level: "beginner" }),
  ).rejects.toMatchObject({ status: 429, retryAfterSeconds: 12 });
});

test("client validates snapshots without model inference", async () => {
  let endpoint = "";
  const client = createTutorClient({
    fetcher: async (url) => {
      endpoint = String(url);
      return new Response("{}", { status: 200 });
    },
  });
  await client.validateContext({
    algorithm: "sort",
    code: "x=1",
    phase: "after",
    run_id: "r",
    language_version: "v1",
  });
  expect(endpoint).toBe("/api/context/validate");
});
