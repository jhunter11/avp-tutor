import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
const demo = JSON.parse(
  readFileSync(new URL("./fixtures/demo.json", import.meta.url), "utf8"),
);

const reply = {
  answer: "The value 4 is saved in key while larger values shift right.",
  sources: [
    {
      id: "insertion-sort:saved-key",
      title: "Insertion sort",
      section: "Saved key",
      path: "knowledge/insertion-sort.md",
      text: "The saved key is kept separately during shifts.",
    },
  ],
  warnings: [],
  context_status: "provided",
  provider: "ollama",
  model: "test-model",
  latency_ms: 150,
  fallback_used: false,
};

async function mockApi(page: Page) {
  await page.route("**/api/health", (route) =>
    route.fulfill({
      json: {
        provider_configured: true,
        provider: "ollama",
        model: "test-model",
      },
    }),
  );
  await page.route("**/api/demo/insertion-sort?*", (route) =>
    route.fulfill({ json: demo }),
  );
  await page.route("**/api/tutor", (route) => route.fulfill({ json: reply }));
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
});

test("workspace loads and step navigation changes highlighted code", async ({
  page,
}) => {
  await expect(
    page.getByRole("heading", { name: "Understand every move." }),
  ).toBeVisible();
  await expect(page.getByLabel("Array:", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await expect(page.locator('[aria-current="step"]')).toContainText(
    "key = collection[i]",
  );
  await expect(page.getByText("Context attached · step 1")).toBeVisible();
});

test("sends exact step, mode, variables and bounded history", async ({
  page,
}) => {
  const requests: any[] = [];
  await page.route("**/api/tutor", (route) => {
    requests.push(route.request().postDataJSON());
    return route.fulfill({ json: reply });
  });
  const shiftIndex = demo.frames.findIndex(
    (f: any) => f.arrays.collection.join(",") === "2,7,9,9",
  );
  await page.getByLabel("Execution step").fill(String(shiftIndex));
  await page.getByRole("button", { name: "Give a hint", exact: true }).click();
  await page.getByLabel("Ask the tutor").fill("Did we lose 4?");
  await page.getByRole("button", { name: "Ask tutor" }).click();
  await expect(page.getByRole("log")).toContainText(reply.answer);
  expect(requests[0].context.variables.key).toBe(4);
  expect(requests[0].context.arrays.collection).toEqual([2, 7, 9, 9]);
  expect(requests[0].context.phase).toBe("after");
  expect(requests[0].mode).toBe("hint");
  expect(requests[0].history).toEqual([]);
  await page.getByLabel("Ask the tutor").fill("Was that a swap?");
  await page.getByRole("button", { name: "Ask tutor" }).click();
  await expect(page.locator(".message.assistant")).toHaveCount(2);
  expect(requests[1].history).toHaveLength(2);
  expect(requests[1].history[0].content).toContain("Did we lose 4?");
});

test("references are expandable and answer is attached to a step", async ({
  page,
}) => {
  await page.getByRole("button", { name: "Explain this step" }).click();
  await expect(page.locator(".message.assistant")).toContainText("Step 0");
  await page.getByText("1 teaching references provided to the model").click();
  await expect(
    page.getByText("The saved key is kept separately during shifts."),
  ).toBeVisible();
});

test("validation error arrays render as a readable error and question is preserved", async ({
  page,
}) => {
  await page.route("**/api/tutor", (route) =>
    route.fulfill({
      status: 422,
      json: { detail: [{ msg: "Invalid context" }] },
    }),
  );
  await page.getByLabel("Ask the tutor").fill("Why?");
  await page.getByRole("button", { name: "Ask tutor" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Check the supplied code",
  );
  await expect(page.getByLabel("Ask the tutor")).toHaveValue("Why?");
  await expect(page.locator(".message")).toHaveCount(0);
});

test("rate limit is actionable", async ({ page }) => {
  await page.route("**/api/tutor", (route) =>
    route.fulfill({ status: 429, body: "Rate limit exceeded" }),
  );
  await page.getByRole("button", { name: "Explain this step" }).click();
  await expect(page.getByRole("alert")).toContainText("Wait a moment");
});

test("network failure allows retry", async ({ page }) => {
  await page.route("**/api/tutor", (route) => route.abort());
  await page.getByLabel("Ask the tutor").fill("Why does key exist?");
  await page.getByRole("button", { name: "Ask tutor" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByLabel("Ask the tutor")).toHaveValue(
    "Why does key exist?",
  );
  await expect(page.getByRole("button", { name: "Ask tutor" })).toBeEnabled();
});

test("empty question is disabled and clear chat resets history", async ({
  page,
}) => {
  await expect(page.getByRole("button", { name: "Ask tutor" })).toBeDisabled();
  await page.getByRole("button", { name: "Explain this step" }).click();
  await expect(page.locator(".message.assistant")).toHaveCount(1);
  await page.getByRole("button", { name: "Clear chat" }).click();
  await expect(page.locator(".message")).toHaveCount(0);
});

test("mobile layout remains inside the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Insertion sort", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
});

test("stopping a request recovers input and does not add an answer", async ({
  page,
}) => {
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/tutor", async (route) => {
    await pending;
    await route.fulfill({ json: reply }).catch(() => {});
  });
  await page.getByLabel("Ask the tutor").fill("Why?");
  await page.getByRole("button", { name: "Ask tutor" }).click();
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  release();
  await expect(page.getByRole("alert")).toContainText("Request stopped");
  await expect(page.locator(".message.assistant")).toHaveCount(0);
});

test("strategy is sent and preparation is disclosed", async ({ page }) => {
  let sent: any;
  await page.route("**/api/tutor", (route) => {
    sent = route.request().postDataJSON();
    return route.fulfill({
      json: {
        ...reply,
        teaching_decision: {
          action: "explain",
          strategy: "analogy",
          reasons: ["Explicit student preference"],
          policy_version: "teaching-policy-v1",
        },
        evidence: { status: "not_checked" },
        code_examples: [],
      },
    });
  });
  await page.getByLabel("Explanation strategy").selectOption("analogy");
  await page.getByRole("button", { name: /Explain this step/ }).click();
  await page.getByText("How this answer was prepared").click();
  expect(sent.strategy).toBe("analogy");
  await expect(page.getByText("Explicit student preference")).toBeVisible();
  await expect(
    page.getByText(/No independent execution or answer verification/),
  ).toBeVisible();
});
