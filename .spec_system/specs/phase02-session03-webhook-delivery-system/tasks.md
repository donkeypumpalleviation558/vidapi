# Task Checklist

**Session ID**: `phase02-session03-webhook-delivery-system`
**Total Tasks**: 18
**Estimated Duration**: 3-4 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0203]` = Session reference (02=phase number, 03=session number)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 2 | 2 | 0 |
| Foundation | 4 | 4 | 0 |
| Implementation | 8 | 8 | 0 |
| Testing | 4 | 4 | 0 |
| **Total** | **18** | **18** | **0** |

---

## Setup (2 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0203] Verify prerequisites met: confirm sessions 01-02 complete, Alembic migrations 001-004 applied, httpx available (`app/core/config.py`)
- [x] T002 [S0203] Add webhook configuration settings: webhook_secret, webhook_timeout_seconds (default 10), webhook_max_retries (default 3), webhook_retry_delays (default [1, 10, 60]) (`app/core/config.py`)

---

## Foundation (4 tasks)

Core structures and base implementations.

- [x] T003 [S0203] [P] Create WebhookAttempt SQLModel table with id, render_id, event, url, status_code, response_body_excerpt, attempt_number, scheduled_at, delivered_at, error, created_at, updated_at (`app/db/webhook_models.py`)
- [x] T004 [S0203] [P] Add callback_url column to Render model for persisting the callback URL independently of composition JSON (`app/db/models.py`)
- [x] T005 [S0203] Create Alembic migration 005 adding webhook_attempts table and renders.callback_url column (`alembic/versions/005_add_webhook_attempts.py`)
- [x] T006 [S0203] Create webhook CRUD helpers: create_attempt, update_attempt_result, list_attempts_by_render_id (`app/db/webhook_crud.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T007 [S0203] Implement webhook payload construction as a pure function producing PRD-specified JSON (event, render_id, status, url, poster, completed_at) (`app/services/webhook_service.py`)
- [x] T008 [S0203] Implement HMAC-SHA256 payload signing with configurable secret, producing X-VidAPI-Signature and X-VidAPI-Timestamp headers, with graceful handling when secret is not configured (`app/services/webhook_service.py`)
- [x] T009 [S0203] Implement single-attempt async webhook delivery via httpx with timeout, response capture (status code, body excerpt up to 500 chars), and WebhookAttempt persistence (`app/services/webhook_service.py`)
- [x] T010 [S0203] Implement retry loop with exponential backoff (1s, 10s, 60s delays via asyncio.sleep), recording each attempt separately, with duplicate-trigger prevention while in-flight (`app/services/webhook_service.py`)
- [x] T011 [S0203] Implement top-level dispatch_webhook function that reads callback_url from render record, skips silently if absent, catches all exceptions to prevent propagation to render pipeline (`app/services/webhook_service.py`)
- [x] T012 [S0203] Update render creation routes to persist callback_url on the Render record when composition includes a callback field (`app/api/routes_renders.py`, `app/api/routes_templates.py`)
- [x] T013 [S0203] Update render_crud.create_render to accept and store callback_url parameter (`app/db/render_crud.py`)
- [x] T014 [S0203] Integrate webhook dispatch into worker pipeline: fire after SUCCEEDED in _execute_pipeline, after FAILED in _mark_failed, and after CANCELLED in _cancel_render, using asyncio.create_task for non-blocking delivery with cleanup on scope exit for all acquired resources (`app/workers/render_worker.py`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T015 [S0203] [P] Write unit tests for webhook payload construction and HMAC signing: correct structure, correct signature for known inputs, missing secret handling (`tests/test_webhook_service.py`)
- [x] T016 [S0203] [P] Write unit tests for webhook delivery and retry: mocked httpx transport for success, timeout, connection error, HTTP 5xx, verify attempt records and backoff delays (`tests/test_webhook_service.py`)
- [x] T017 [S0203] [P] Write integration tests for webhook CRUD: create_attempt, update_attempt_result, list_attempts_by_render_id, verify all fields persisted correctly (`tests/test_webhook_crud.py`)
- [x] T018 [S0203] Run full test suite, verify all new and existing tests pass, validate ASCII encoding on all new files (`tests/`)

---

## Completion Checklist

Before marking session complete:

- [x] All tasks marked `[x]`
- [x] All tests passing (457/457)
- [x] All files ASCII-encoded
- [x] implementation-notes.md updated
- [x] Ready for the validate workflow step

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
