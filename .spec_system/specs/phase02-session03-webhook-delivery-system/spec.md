# Session Specification

**Session ID**: `phase02-session03-webhook-delivery-system`
**Phase**: 02 - Templates and Polish
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session implements webhook callback delivery so VidAPI clients receive reliable HTTP notifications when renders reach terminal states (succeeded, failed, cancelled). The system signs every payload with HMAC-SHA256, retries failed deliveries with exponential backoff, and stores a full audit trail of every delivery attempt.

Webhooks are the primary mechanism for clients to avoid polling. The Composition model already carries an optional `callback` field, but no delivery infrastructure exists yet. This session builds the database model, delivery service, signing logic, retry mechanism, and worker pipeline integration to close that gap.

This is a backend-only session producing application code with no UI component. It touches the database layer (new table + migration), a new service module, configuration additions, and the worker pipeline's terminal-state handling.

---

## 2. Objectives

1. Persist a `webhook_attempts` table that records every delivery attempt with status, timing, and response metadata.
2. Implement an async webhook delivery service that constructs PRD-specified payloads, signs them with HMAC-SHA256, and delivers via httpx.
3. Retry failed webhook deliveries up to 3 times with exponential backoff delays of 1s, 10s, and 60s.
4. Integrate webhook dispatch into the worker pipeline so it fires automatically after any terminal render status without blocking the render itself.

---

## 3. Prerequisites

### Required Sessions
- [x] `phase02-session01-template-models-and-crud-api` - Template CRUD and DB models
- [x] `phase02-session02-template-variables-and-rendering` - Template variable substitution and rendering

### Required Tools/Knowledge
- httpx async HTTP client (already a project dependency)
- HMAC-SHA256 signing (Python stdlib hmac/hashlib)
- Alembic migrations (existing pattern from migrations 001-004)

### Environment Requirements
- SQLite dev database with Alembic migrations applied
- Redis + ARQ worker for async render pipeline

---

## 4. Scope

### In Scope (MVP)
- WebhookAttempt SQLModel table with id, render_id, event, url, status_code, response_body_excerpt, attempt_number, scheduled_at, delivered_at, error, created_at, updated_at
- Alembic migration 005 for webhook_attempts table
- Add callback_url column to renders table so the callback URL persists independently of the composition JSON
- Webhook service (`app/services/webhook_service.py`) with async delivery via httpx
- HMAC-SHA256 payload signing with configurable secret via WEBHOOK_SECRET setting
- X-VidAPI-Signature and X-VidAPI-Timestamp headers on outbound requests
- Webhook events: render.succeeded, render.failed, render.cancelled
- Webhook payload format per PRD specification (event, render_id, status, url, poster, completed_at)
- Exponential backoff retry: 3 attempts at delays of 1s, 10s, 60s
- Store every delivery attempt in webhook_attempts for audit
- Non-blocking delivery: webhook dispatch runs after render status update, never blocks terminal transition
- Worker integration: dispatch webhook in run_render after SUCCEEDED, in _mark_failed after FAILED, and in _cancel_render after CANCELLED
- Webhook CRUD helper (`app/db/webhook_crud.py`) for creating and querying attempts
- Configuration additions: WEBHOOK_SECRET, WEBHOOK_TIMEOUT_SECONDS, WEBHOOK_MAX_RETRIES

### Out of Scope (Deferred)
- Webhook management API endpoints (list/inspect attempts) - *Reason: Phase 03 operational visibility*
- Custom webhook headers or authentication beyond HMAC - *Reason: not in Phase 02 PRD*
- Webhook event filtering or subscription management - *Reason: future phase*
- ARQ-based retry scheduling (using in-process retry loop for MVP simplicity) - *Reason: ARQ retry adds complexity; in-process backoff is sufficient for MVP*

---

## 5. Technical Approach

### Architecture
The webhook system follows a fire-and-forget pattern from the worker's perspective. After a render reaches a terminal state, the worker calls `webhook_service.dispatch_webhook()` which:
1. Reads the callback URL from the render record
2. Constructs the event payload per PRD spec
3. Signs the payload with HMAC-SHA256
4. Attempts delivery via httpx with timeout
5. Records the attempt in webhook_attempts
6. On failure, retries with exponential backoff (1s, 10s, 60s)
7. Each retry is recorded as a separate attempt

The dispatch is wrapped in a try/except so webhook failures never propagate to the render pipeline. Webhook success/failure is independent of render success/failure.

### Design Patterns
- **Service pattern**: WebhookService encapsulates all delivery logic, consistent with existing RenderService/TemplateService/AssetService
- **Audit trail**: Every HTTP attempt is persisted before the request is made, then updated with the result
- **Fail-safe**: All webhook errors are caught and logged; never affect render status
- **Pure-function payload construction**: Payload building is a testable pure function separate from delivery

### Technology Stack
- Python 3.11+ with async/await
- httpx (existing dependency) for async HTTP delivery
- hmac + hashlib (stdlib) for HMAC-SHA256 signing
- SQLModel for WebhookAttempt table
- Alembic for migration
- structlog for structured logging
- asyncio.sleep for retry backoff delays

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/db/webhook_models.py` | WebhookAttempt SQLModel table definition | ~50 |
| `app/db/webhook_crud.py` | CRUD helpers for webhook_attempts table | ~80 |
| `app/services/webhook_service.py` | Webhook delivery service with signing, retry, and audit | ~200 |
| `alembic/versions/005_add_webhook_attempts.py` | Migration for webhook_attempts table + renders.callback_url | ~50 |
| `tests/test_webhook_service.py` | Unit and integration tests for webhook delivery | ~250 |
| `tests/test_webhook_crud.py` | CRUD tests for webhook_attempts | ~80 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/core/config.py` | Add webhook_secret, webhook_timeout, webhook_max_retries settings | ~10 |
| `app/db/models.py` | Add callback_url field to Render model | ~5 |
| `app/workers/render_worker.py` | Add webhook dispatch after terminal states | ~30 |
| `app/db/render_crud.py` | Add update for callback_url in create_render | ~5 |
| `app/api/routes_renders.py` | Persist callback_url on render creation | ~5 |
| `app/api/routes_templates.py` | Persist callback_url on template render creation | ~5 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Webhook fires on render.succeeded with correct PRD payload
- [ ] Webhook fires on render.failed with correct PRD payload
- [ ] Webhook fires on render.cancelled with correct PRD payload
- [ ] Payloads are signed with HMAC-SHA256
- [ ] X-VidAPI-Signature and X-VidAPI-Timestamp headers are present
- [ ] Failed deliveries retry up to 3 times with 1s, 10s, 60s delays
- [ ] Every delivery attempt is stored in webhook_attempts table
- [ ] Webhook delivery never blocks render status updates
- [ ] Webhook failure does not affect render success status
- [ ] Renders without a callback URL skip webhook dispatch silently

### Testing Requirements
- [ ] Unit tests for payload construction and HMAC signing
- [ ] Unit tests for retry logic with mocked httpx
- [ ] Integration tests for webhook_attempts CRUD
- [ ] Integration test for worker pipeline webhook dispatch
- [ ] Edge case tests: no callback URL, unreachable endpoint, timeout, invalid URL

### Non-Functional Requirements
- [ ] Webhook delivery completes within 5 minutes including all retries
- [ ] Webhook timeout per attempt is configurable (default 10s)

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (snake_case, type hints, service pattern)
- [ ] No webhook errors propagate to render pipeline

---

## 8. Implementation Notes

### Key Considerations
- The Composition model already has `callback: HttpUrl | None` but the Render DB model does not persist it. We need a `callback_url` column on renders so the worker can read the URL without re-parsing the full composition JSON.
- HMAC signing uses `hmac.new(key, msg, hashlib.sha256).hexdigest()`. The message is the raw JSON payload bytes. The key is WEBHOOK_SECRET from settings.
- Retry delays (1s, 10s, 60s) are implemented with asyncio.sleep inside the dispatch function. Since webhook dispatch is non-blocking to the render pipeline, this is acceptable for MVP.
- The response_body_excerpt field stores up to 500 chars of the webhook endpoint's response body for debugging failed deliveries.

### Potential Challenges
- **Webhook endpoint unreachable**: Mitigation -- timeout per attempt, max 3 retries, log and store all attempts
- **Long retry delays blocking worker**: Mitigation -- dispatch runs in a background task, worker does not await completion
- **HMAC secret not configured**: Mitigation -- if WEBHOOK_SECRET is empty/None, skip signing and log a warning

### Relevant Considerations
- [P01] **Worker drives status transitions externally**: Webhook dispatch follows the same pattern -- worker triggers dispatch after terminal status transition, keeping the service stateless.
- [P01] **Rate-limited progress updates**: Same principle applies -- webhook delivery is rate-limited by the retry backoff schedule.
- [P00] **Atomic file writes**: Webhook attempts use DB writes (not files), but the same principle of recording state before action applies -- create the attempt record before making the HTTP request.

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Webhook dispatch must never raise into the render pipeline (fail-safe boundary)
- Retry loop must handle all httpx exceptions (timeout, connection, HTTP errors)
- HMAC signing must handle missing/empty secret gracefully (skip or warn, never crash)

---

## 9. Testing Strategy

### Unit Tests
- Payload construction produces correct JSON structure per PRD
- HMAC signing produces correct signature for known inputs
- Retry delays match expected backoff schedule (1s, 10s, 60s)
- Dispatch skips silently when callback_url is None
- Dispatch handles httpx.TimeoutException, httpx.ConnectError, HTTP 4xx/5xx

### Integration Tests
- WebhookAttempt CRUD: create, query by render_id, query by event
- Full dispatch cycle with mocked httpx transport
- Worker pipeline fires webhook on SUCCEEDED terminal state

### Manual Testing
- Submit a render with callback URL pointing to a local echo server
- Verify webhook payload, headers, and signature arrive correctly
- Submit a render with unreachable callback URL, verify 3 attempts logged

### Edge Cases
- Render with no callback URL (no webhook fired, no error)
- Callback URL that returns 500 on first attempt, 200 on second
- Callback URL that times out on every attempt
- Very large render_id or URL values
- WEBHOOK_SECRET not configured (delivery works unsigned or skips signing)
- Concurrent webhooks from multiple workers

---

## 10. Dependencies

### External Libraries
- httpx: existing dependency (async HTTP client)
- hmac + hashlib: Python stdlib
- asyncio: Python stdlib

### Other Sessions
- **Depends on**: phase02-session01, phase02-session02 (template CRUD, rendering pipeline)
- **Depended by**: phase02-session05-audio-polish-and-hardening (indirectly, as session 04 depends on session 03)

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
