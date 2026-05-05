# Local Dev Testing Anomalies - 2026-05-05

## Context

- Local stack was started with `scripts/dev.sh`.
- Target URL: `http://127.0.0.1:8005`.
- Test evidence: `dogfood-output/vidapi-local-20260505/`.
- Browser session: closed after testing.
- Automated test result: `scripts/dev.sh test` passed with `785 passed, 1 skipped`.

## Confirmed Issues

### 1. Generic render artifact endpoint returns 404 for published artifacts

**Severity:** Medium
**Area:** API / artifact retrieval
**Status:** Confirmed in local dev

The OpenAPI surface exposes `GET /v1/renders/{render_id}/artifacts/{artifact_name}` as a generic artifact download endpoint. A smoke render completed successfully and exposed working direct artifact routes:

- `GET /v1/renders/render_mosxzjxf96303yrw/download` returned `200 video/mp4`.
- `GET /v1/renders/render_mosxzjxf96303yrw/poster` returned `200 image/jpeg`.
- The worker log reported publishing artifacts including `input.json`, `expanded.json`, `compiled.editly.json`, `replay.json`, `output`, `poster.jpg`, and `logs.txt`.

The generic artifact endpoint returned `404 application/json` for every known or likely artifact name tested:

- `output`
- `output.mp4`
- `render_mosxzjxf96303yrw.mp4`
- `poster`
- `poster.jpg`
- `render_mosxzjxf96303yrw.jpg`
- `input`
- `input.json`
- `expanded`
- `expanded.json`
- `compiled`
- `compiled.editly.json`
- `replay`
- `replay.json`
- `logs`
- `logs.txt`

**Impact:** clients cannot use the documented generic artifact route, even though the render and direct download/poster routes work.

**Evidence:**

- `dogfood-output/vidapi-local-20260505/evidence-artifact-output-404.txt`
- `dogfood-output/vidapi-local-20260505/evidence-artifact-logs-404.txt`
- `dogfood-output/vidapi-local-20260505/evidence-download-headers.txt`
- `dogfood-output/vidapi-local-20260505/render-status.json`
- `dogfood-output/vidapi-local-20260505/screenshots/artifact-endpoint-docs.png`

**Suggested follow-up:** verify how artifact names are stored in the DB/storage layer and align the route lookup with the names returned or documented for clients.

## Warnings And Observations

### 2. Render status reports `duration: null` for a valid one-second MP4

**Severity:** Low / needs product decision
**Area:** API response metadata
**Status:** Observed, not counted as a confirmed defect

The completed render status payload reported `"duration": null`, while the downloaded MP4 probed as exactly `1.000000` seconds with `ffprobe`.

**Impact:** client UIs may not be able to display media duration from the render status response.

**Reason not counted as a defect:** the contract is ambiguous. It is not clear whether `duration` means output media duration, render execution duration, or an optional field that can be null.

**Suggested follow-up:** decide the intended meaning of `duration`; either populate it for completed media or rename/split fields to avoid ambiguity.

### 3. OpenAPI advertises API-key security while local dev accepts unauthenticated requests

**Severity:** Low
**Area:** Local dev API docs / auth UX
**Status:** Observed

Local dev has `API_KEY_AUTH_ENABLED=false`, and unauthenticated calls to render/template endpoints succeeded. The OpenAPI schema still marks these endpoints with `APIKeyAuth`, so Swagger shows auth controls even though no key is required locally.

**Impact:** local testers may think they need an API key when they do not, or may miss that production behavior differs.

**Suggested follow-up:** document the local-vs-production auth behavior clearly in the Swagger description or dev docs. If supported by the framework, consider making the local OpenAPI security display reflect the active auth mode.

### 4. `HEAD /v1/renders/{id}/download` returns 405

**Severity:** Low / compatibility note
**Area:** API ergonomics
**Status:** Observed, likely contract-compliant

`HEAD /v1/renders/render_mosxzjxf96303yrw/download` returned `405 Method Not Allowed` with `allow: GET`. OpenAPI only advertises `GET`, so this is not necessarily a bug.

**Impact:** some clients, download managers, or proxies may use `HEAD` to inspect file metadata before downloading.

**Suggested follow-up:** leave as-is if strict OpenAPI behavior is intended. Add `HEAD` support if artifact metadata probing is useful for client integrations.

### 5. Swagger UI depends on external CDN assets

**Severity:** Low
**Area:** Local dev docs reliability
**Status:** Observed

Swagger UI loaded these external assets:

- `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css`
- `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js`
- `https://fastapi.tiangolo.com/img/favicon.png`

**Impact:** local API docs may degrade or fail when offline, behind strict firewalls, or if CDN access is blocked.

**Suggested follow-up:** accept this as standard FastAPI behavior, or serve Swagger UI assets locally if offline development is a requirement.

### 6. `editly` is not on PATH in the tested local environment

**Severity:** Medium environment risk
**Area:** Renderer tooling
**Status:** Observed environment warning

`hyperframes` is available on PATH, but `editly` is not. The dev script warns that default non-HTML renders use Editly and recommends either installing Editly or requesting `renderer=ffmpeg-native`.

The smoke render explicitly used `renderer=ffmpeg-native`, so this did not block the tested workflow.

**Impact:** default render requests may fail locally if they select the Editly renderer.

**Suggested follow-up:** install `editly` for full local coverage, make `ffmpeg-native` the documented local default, or add a clearer startup health warning for renderer availability.

### 7. `scripts/dev.sh` is untracked even though it is the dev startup path

**Severity:** Low repo hygiene
**Area:** Project workflow
**Status:** Observed via `git status --short`

`git status --short` reported:

```text
?? scripts/dev.sh
```

The same script is the local startup entrypoint used for this test run.

**Impact:** if this script is intended to be shared by the team or CI-adjacent workflows, leaving it untracked makes local setup non-reproducible for other clones.

**Suggested follow-up:** commit `scripts/dev.sh` if it is intended project tooling; otherwise document that it is a local-only helper.

### 8. Test run left local render data behind

**Severity:** Low local-state note
**Area:** Local dev data hygiene
**Status:** Expected side effect

The smoke test created a successful render record:

```text
render_mosxzjxf96303yrw
```

Templates created during the smoke test were soft-deleted and no longer appear in the template list, but the successful render remains in local dev state and operations counts.

**Impact:** subsequent local tests may see one succeeded render in list/ops endpoints.

**Suggested follow-up:** add a documented cleanup command for local smoke-test data if zero-state local testing is important.

## Non-Issues Confirmed During Testing

- `/v1/health` returned healthy database and Redis state.
- Swagger UI loaded and had no browser console/page errors during the run.
- Template CRUD worked after corrected shell parsing.
- Invalid template payload returned useful `422` validation errors.
- The `ffmpeg-native` worker path completed successfully.
- The downloaded MP4 and poster file were valid media files.
- Ops status counts reflected the successful render.
- Full pytest suite passed.
