# Task Checklist

**Session ID**: `phase01-session03-progress-tracking-and-cancellation`
**Total Tasks**: 21
**Estimated Duration**: 2.5-3.5 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0103]` = Session reference (Phase 01, Session 03)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 2 | 2 | 0 |
| Foundation | 6 | 6 | 0 |
| Implementation | 8 | 8 | 0 |
| Testing | 5 | 5 | 0 |
| **Total** | **21** | **21** | **0** |

---

## Setup (2 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0103] Verify prerequisites met: existing 264 tests pass, Redis available, async render path functional
- [x] T002 [S0103] Add `progress_update_interval_seconds` setting to config and `cancel_requested_at` column to Render DB model (`app/core/config.py`, `app/db/models.py`)

---

## Foundation (6 tasks)

Core structures and base implementations.

- [x] T003 [S0103] [P] Create FFmpeg stderr progress parser module with time-based extraction, percentage calculation against total duration, and graceful fallback on malformed lines (`app/services/ffmpeg_progress.py`)
- [x] T004 [S0103] [P] Extend RenderStatus state machine with CANCELLED transitions from FETCHING, COMPILING, RENDERING, UPLOADING states (`app/models/render.py`)
- [x] T005 [S0103] [P] Add RenderListResponse, RenderListItem, and RenderListParams pagination query models (`app/models/render.py`)
- [x] T006 [S0103] Add list_renders CRUD function with offset/limit pagination, deterministic ordering, and optional status filter (`app/db/render_crud.py`)
- [x] T007 [S0103] Add set_cancel_requested and update_render_progress CRUD functions with idempotency protection (`app/db/render_crud.py`)
- [x] T008 [S0103] [P] Add RENDER_CANCELLED error code to registry and register CancelledError mapping (`app/models/error_codes.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T009 [S0103] Refactor EditlyRenderer.render() to stream stderr line-by-line via asyncio readline, accept optional progress callback, with cleanup on scope exit for all acquired resources (`app/renderers/editly.py`)
- [x] T010 [S0103] Create worker progress callback that parses FFmpeg lines, computes percentage, and updates DB progress with rate-limiting (>= 2% delta or interval threshold), with timeout and failure-path handling on DB writes (`app/workers/render_worker.py`)
- [x] T011 [S0103] Implement GET /v1/renders list endpoint with bounded pagination, validated filters, and deterministic ordering by created_at DESC (`app/api/routes_renders.py`)
- [x] T012 [S0103] Implement DELETE /v1/renders/{id} cancellation endpoint with duplicate-trigger prevention while in-flight and idempotent handling for already-cancelled renders (`app/api/routes_renders.py`)
- [x] T013 [S0103] Add cancellation checkpoint function to worker that checks cancel_requested_at between pipeline stages and transitions to CANCELLED with state reset on re-entry (`app/workers/render_worker.py`)
- [x] T014 [S0103] Handle subprocess termination on cancellation during rendering stage: SIGTERM with grace period then SIGKILL, with cleanup on scope exit for process resources (`app/renderers/editly.py`)
- [x] T015 [S0103] Update worker pre-flight check to skip cancelled renders on pickup before entering pipeline (`app/workers/render_worker.py`)
- [x] T016 [S0103] Compute total duration from composition timeline and pass to progress callback for percentage calculation (`app/workers/render_worker.py`)

---

## Testing (5 tasks)

Verification and quality assurance.

- [x] T017 [S0103] [P] Write unit tests for FFmpeg progress parser: normal time output, malformed lines, empty input, zero duration, negative time, 100% boundary, very long duration (`tests/test_ffmpeg_progress.py`)
- [x] T018 [S0103] [P] Write tests for GET /v1/renders list endpoint: empty list, multiple renders, offset/limit pagination, status filter, invalid status, out-of-range offset (`tests/test_render_list.py`)
- [x] T019 [S0103] [P] Write tests for DELETE /v1/renders/{id}: cancel queued render, cancel running render (mock), cancel not-found, cancel already-terminal, idempotent re-cancel, cancel succeeded render rejected (`tests/test_cancellation.py`)
- [x] T020 [S0103] Run full test suite and verify all tests pass including existing 264 tests
- [x] T021 [S0103] Validate ASCII encoding on all new and modified files, verify Unix LF line endings

---

## Completion Checklist

Before marking session complete:

- [x] All tasks marked `[x]`
- [x] All tests passing
- [x] All files ASCII-encoded
- [x] implementation-notes.md updated
- [x] Ready for the validate workflow step

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
