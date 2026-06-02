import { expect, test } from "@playwright/test";

const API = "http://localhost:8000";

const mockQuery = {
  session_id: "e2e-session-001",
  answer: "Guideline excerpt states Bedaquiline under DOTS [1].\n\n_Disclaimer._",
  citations: [
    {
      index: 1,
      chunk_id: "sha256:e2e::p1::c1",
      document_title: "TB Guidelines",
      verification_status: "unverified",
    },
  ],
  model_used: "mock-groq",
  refused: false,
  retrieval_ms: 12,
  out_of_corpus: false,
  suggested_queries: [],
};

const mockChunk = {
  chunk_id: "sha256:e2e::p1::c1",
  source_url: "https://example.org/tb",
  document_title: "TB Guidelines",
  publication_year: 2026,
  page_number: 1,
  exact_context: "Administer Bedaquiline under monitored DOTS.",
  verification_status: "unverified",
  source_org: "ICMR",
  content_hash: null,
};

const mockStarters = [
  {
    id: "s1",
    label: "TB screening under DOTS",
    query: "What does Nature research say about bedaquiline-resistant TB?",
    kind: "corpus",
    source_org: "Nature",
  },
  {
    id: "s2",
    label: "Asthma COPD overlap",
    query: "Summarize asthma COPD overlap screening from Nature.",
    kind: "corpus",
    source_org: "Nature",
  },
  {
    id: "s3",
    label: "How much pizza can a 2-year-old eat in 3 days?",
    query: "How much pizza can a 2 year old kid eat in 3 days?",
    kind: "off_topic",
  },
];

test.beforeEach(async ({ page }) => {
  await page.route(`${API}/health`, async (route) => {
    await route.fulfill({ json: { status: "ok", chroma: "reachable" } });
  });
  await page.route(`${API}/api/v1/suggestions`, async (route) => {
    await route.fulfill({ json: [] });
  });
  await page.route(`${API}/api/v1/starter-prompts`, async (route) => {
    await route.fulfill({ json: mockStarters });
  });
});

test("6.6.1 query → verify → export enabled", async ({ page }) => {
  let verified = false;

  await page.route(`${API}/api/v1/query`, async (route) => {
    await route.fulfill({ json: mockQuery });
  });
  await page.route(`${API}/api/v1/chunks/*`, async (route) => {
    await route.fulfill({
      json: { ...mockChunk, verification_status: verified ? "verified" : "unverified" },
    });
  });
  await page.route(`${API}/api/v1/sessions/*/export-gate`, async (route) => {
    await route.fulfill({
      json: verified
        ? { allowed: true, total: 1, verified: 1, pending_indices: [] }
        : { allowed: false, total: 1, verified: 0, pending_indices: [1] },
    });
  });
  await page.route(`${API}/api/v1/sessions/*/verify/*`, async (route) => {
    verified = true;
    await route.fulfill({ json: { status: "ok", chunk_id: mockChunk.chunk_id } });
  });

  await page.goto("/");
  await expect(page.getByTestId("glass-landing")).toBeVisible();
  await page.getByTestId("query-input").fill("Bedaquiline DOTS");
  await page.getByTestId("btn-submit-query").click();
  await expect(page.getByTestId("query-result")).toBeVisible();
  await expect(page.getByTestId("export-gate-locked")).toBeVisible();
  await expect(page.getByTestId("btn-copy")).toBeDisabled();
  await expect(page.getByTestId("btn-share")).toBeDisabled();

  await expect(page.getByTestId("cite-verify-1")).toContainText("Review above article");
  await page.getByTestId("cite-verify-1").click();

  await expect(page.getByTestId("cite-verified-1")).toBeVisible();
  await expect(page.getByTestId("export-gate-open")).toBeVisible();
  await expect(page.getByTestId("btn-copy")).toBeEnabled();
  await page.getByTestId("btn-share").click();
  await expect(page.getByTestId("share-bar")).toBeVisible();
  await expect(page.getByTestId("share-whatsapp")).toBeVisible();
});

test("6.6.2 export stays locked with unverified citation", async ({ page }) => {
  await page.route(`${API}/api/v1/query`, async (route) => {
    await route.fulfill({ json: mockQuery });
  });
  await page.route(`${API}/api/v1/chunks/*`, async (route) => {
    await route.fulfill({ json: mockChunk });
  });
  await page.route(`${API}/api/v1/sessions/*/export-gate`, async (route) => {
    await route.fulfill({
      json: { allowed: false, total: 1, verified: 0, pending_indices: [1] },
    });
  });

  await page.goto("/");
  await page.getByTestId("query-input").fill("Test");
  await page.getByTestId("btn-submit-query").click();
  await expect(page.getByTestId("btn-copy")).toBeDisabled();
  await expect(page.getByTestId("btn-export")).toHaveCount(0);
});

test("6.6.3 trust nudge and source preview on citation click", async ({ page }) => {
  await page.route(`${API}/api/v1/query`, async (route) => {
    await route.fulfill({ json: mockQuery });
  });
  await page.route(`${API}/api/v1/chunks/*`, async (route) => {
    await route.fulfill({ json: mockChunk });
  });
  await page.route(`${API}/api/v1/sessions/*/export-gate`, async (route) => {
    await route.fulfill({
      json: { allowed: false, total: 1, verified: 0, pending_indices: [1] },
    });
  });

  await page.goto("/");
  await page.getByTestId("query-input").fill("Test");
  await page.getByTestId("btn-submit-query").click();
  await expect(page.getByTestId("cite-verify-1")).toContainText("Review above article");
  await page.getByTestId("citation-row-1").click();
  await expect(page.getByTestId("citation-row-1")).toHaveClass(/selected/);
  await expect(page.getByTestId("source-preview-panel")).toBeVisible();
  await expect(page.getByTestId("context-highlight-box")).toBeVisible();
});

test("6.6.6 export toolbar visible but locked until verified", async ({ page }) => {
  await page.route(`${API}/api/v1/query`, async (route) => {
    await route.fulfill({ json: mockQuery });
  });
  await page.route(`${API}/api/v1/chunks/*`, async (route) => {
    await route.fulfill({ json: mockChunk });
  });
  await page.route(`${API}/api/v1/sessions/*/export-gate`, async (route) => {
    await route.fulfill({
      json: { allowed: false, total: 1, verified: 0, pending_indices: [1] },
    });
  });

  await page.goto("/");
  await expect(page.getByTestId("btn-copy")).toHaveCount(0);
  await page.getByTestId("query-input").fill("Test");
  await page.getByTestId("btn-submit-query").click();
  await expect(page.getByTestId("export-toolbar")).toBeVisible();
  await expect(page.getByTestId("btn-copy")).toBeDisabled();
});

test("6.6.7 out-of-corpus hides citations and export toolbar", async ({ page }) => {
  await page.route(`${API}/api/v1/query`, async (route) => {
    await route.fulfill({
      json: {
        session_id: "e2e-ooc",
        answer:
          "I made a Pinky promise that I will never ever give Inavlid response\n\nTry one of these verified topics:",
        citations: [],
        model_used: "none",
        refused: true,
        retrieval_ms: 1,
        out_of_corpus: true,
        suggested_queries: [
          {
            label: "TB DOTS",
            query: "Bedaquiline DOTS",
            chunk_id: "sha256:e2e::p1::c1",
            source_org: "ICMR",
          },
        ],
      },
    });
  });

  await page.goto("/");
  await page.getByTestId("query-input").fill("quantum physics");
  await page.getByTestId("btn-submit-query").click();
  await expect(page.getByTestId("pinky-promise")).toBeVisible();
  await expect(page.getByTestId("export-toolbar")).toHaveCount(0);
  await expect(page.getByTestId("validation-pane")).toHaveCount(0);
});
