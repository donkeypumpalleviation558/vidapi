# Task Checklist

**Session ID**: `phase01-session01-redis-arq-queue-integration`
**Total Tasks**: 20
**Estimated Duration**: 2.5-3.5 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0101]` = Session reference (Phase 01, Session 01)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 3 | 3 | 0 |
| Foundation | 5 | 5 | 0 |
| Implementation | 8 | 8 | 0 |
| Testing | 4 | 4 | 0 |
| **Total** | **20** | **20** | **0** |

---

## Setup (3 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0101] Add arq and redis[hiredis] dependencies to pyproject.toml (`pyproject.toml`)
- [x] T002 [S0101] Add REDIS_URL and RENDER_MODE settings to config (`app/core/config.py`)
- [x] T003 [S0101] Verify Redis is available locally via Docker or system install

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T004 [S0101] Create Redis connection pool module with create/close lifecycle (`app/core/redis.py`)
- [x] T005 [S0101] Create ARQ worker task function that loads render and calls execute_render with timeout, retry/backoff, and failure-path handling (`app/workers/render_worker.py`)
- [x] T006 [S0101] Create ARQ WorkerSettings class with task registration and on_startup/on_shutdown hooks (`app/workers/arq_settings.py`)
- [x] T007 [S0101] Ensure RenderStatus.QUEUED is properly defined in render model (`app/models/render.py`)
- [x] T008 [S0101] Add Redis pool lifecycle to FastAPI lifespan (create on startup, close on shutdown) (`app/main.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T009 [S0101] Create enqueue_render helper that pushes job to ARQ with render_id argument (`app/workers/render_worker.py`)
- [x] T010 [S0101] Add ARQ pool as a FastAPI dependency for route injection (`app/api/deps.py`)
- [x] T011 [S0101] Modify POST /v1/renders to create DB record with status queued, then enqueue via ARQ when RENDER_MODE=async, with duplicate-trigger prevention while in-flight (`app/api/routes_renders.py`)
- [x] T012 [S0101] Preserve sync render path in POST /v1/renders when RENDER_MODE=sync (`app/api/routes_renders.py`)
- [x] T013 [S0101] Handle Redis connection failure on enqueue with 503 response and explicit error mapping (`app/api/routes_renders.py`)
- [x] T014 [S0101] Wire worker DB session factory using shared engine initialization (`app/workers/render_worker.py`)
- [x] T015 [S0101] Add optional Redis health info to GET /v1/health with timeout and failure-path handling (`app/api/routes_health.py`)
- [x] T016 [S0101] Export worker __init__ and update app.workers package (`app/workers/__init__.py`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T017 [S0101] [P] Write unit tests for enqueue path with mocked Redis/ARQ pool (`tests/test_worker_enqueue.py`)
- [x] T018 [S0101] [P] Write unit tests for worker task function with mocked RenderService (`tests/test_worker_enqueue.py`)
- [x] T019 [S0101] Run full test suite and verify existing tests pass unchanged in sync mode
- [x] T020 [S0101] Validate ASCII encoding and LF line endings on all new/modified files

---

## Completion Checklist

Before marking session complete:

- [x] All tasks marked `[x]`
- [x] All tests passing (235/235)
- [x] All files ASCII-encoded
- [x] implementation-notes.md updated
- [x] Ready for the validate workflow step

---

## Next Steps

Run the validate workflow step to verify session completeness.
