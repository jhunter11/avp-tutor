import { test, expect } from "@playwright/test";

// Optional live integration tests; start the backend and run E2E_LIVE=1.
test("real backend serves a trace that the UI can step through", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByLabel("Array:", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await expect(page.locator('[aria-current="step"]')).toContainText(
    "key = collection[i]",
  );
});

test("real backend accepts imported execution snapshots", async ({ page }) => {
  await page.goto("/");
  await page.getByText("Change input or connect your visualizer").click();
  await page
    .getByLabel("Execution snapshot JSON")
    .fill(
      JSON.stringify({
        algorithm: "binary_search",
        code: "low = 0",
        current_line: 1,
        phase: "after",
        variables: { low: 0 },
      }),
    );
  await page.getByRole("button", { name: "Use snapshot" }).click();
  await expect(page.getByText("Imported snapshot")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "binary search", exact: true }),
  ).toBeVisible();
});
