# Task Checklist

**Session ID**: `phase01-session02-worker-render-pipeline`
**Total Tasks**: 20
**Estimated Duration**: 2.5-3.5 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0102]` = Session reference (Phase 01, Session 02)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 2 | 2 | 0 |
| Foundation | 5 | 5 | 0 |
| Implementation | 9 | 9 | 0 |
| Testing | 4 | 4 | 0 |
| **Total** | **20** | **20** | **0** |

---

## Setup (2 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0102] Verify prerequisites met -- Redis running, 235 existing tests passing, Session 01 artifacts present (`app/workers/render_worker.py`, `app/core/redis.py`)
- [x] T002 [S0102] Create directory structure for new source and test files (`app/models/error_codes.py`, `app/workers/workspace.py`, `app/workers/log_collector.py`)

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T003 [S0102] [P] Create error codes registry with stable machine-readable codes for all failure modes -- RENDER_TIMEOUT, COMPILE_ERROR, RENDER_ERROR, ASSET_FETCH_ERROR, MERGE_ERROR, STORAGE_ERROR, NO_INPUT_DATA, INPUT_FILE_MISSING, QUEUE_UNAVAILABLE, WORKER_UNEXPECTED_ERROR, INVALID_COMPOSITION (`app/models/error_codes.py`)
- [x] T004 [S0102] [P] Create workspace lifecycle manager with create, persist_artifacts, and cleanup methods, with cleanup on scope exit for all acquired resources (`app/workers/workspace.py`)
- [x] T005 [S0102] [P] Create per-render log collector that aggregates structured entries across pipeline stages and flushes to logs.txt, with explicit loading, empty, error, and offline states (`app/workers/log_collector.py`)
- [x] T006 [S0102] Add workspace cleanup settings -- workspace_cleanup_enabled (bool, default true), workspace_cleanup_keep_on_failure (bool, default true) (`app/core/config.py`)
- [x] T007 [S0102] Refactor RenderService to expose individual stage methods (stage_validate_and_expand, stage_resolve_and_compile, stage_render_and_store) that accept render_id parameter instead of creating their own record, preserving sync convenience method (`app/services/render_service.py`)

---

## Implementation (9 tasks)

Main feature implementation.

- [x] T008 [S0102] Rewrite worker run_render to drive stage-by-stage status transitions (QUEUED->FETCHING->COMPILING->RENDERING->UPLOADING->SUCCEEDED), calling refactored RenderService stage methods with render_id, with duplicate-trigger prevention while in-flight (`app/workers/render_worker.py`)
- [x] T009 [S0102] Implement workspace cleanup in workspace manager -- remove temp files after artifacts persisted, preserve input.json/logs.txt/compiled spec on failure for debugging, with cleanup on scope exit for all acquired resources (`app/workers/workspace.py`)
- [x] T010 [S0102] Integrate log collector into worker pipeline -- capture entries at each stage transition (fetching, compiling, rendering, uploading), flush to logs.txt on completion or failure (`app/workers/render_worker.py`)
- [x] T011 [S0102] Map all failure modes to normalized error codes from the registry -- RenderServiceError, CompileError, RenderError, TimeoutError, OSError, and unexpected exceptions, with explicit error mapping (`app/workers/render_worker.py`)
- [x] T012 [S0102] Configure ARQ retry semantics -- max_tries=1 (renders are not idempotent), job_timeout from settings, health_check_interval=30s, with timeout, retry/backoff, and failure-path handling (`app/workers/arq_settings.py`)
- [x] T013 [S0102] Update worker startup to initialize workspace manager and log collector in ARQ context, with cleanup on scope exit for all acquired resources (`app/workers/arq_settings.py`)
- [x] T014 [S0102] Update sync render path in routes_renders.py for compatibility with refactored RenderService stage methods (`app/api/routes_renders.py`)
- [x] T015 [S0102] Ensure started_at is set on FETCHING transition and completed_at on any terminal state transition in render_crud (`app/db/render_crud.py`)
- [x] T016 [S0102] Wire workspace cleanup into worker finally block -- cleanup runs even on timeout or crash, does not raise on cleanup errors, with cleanup on scope exit for all acquired resources (`app/workers/render_worker.py`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T017 [S0102] [P] Write unit tests for worker pipeline -- status transitions through all stages, FAILED on each error type, error code normalization, log collector integration (`tests/test_worker_pipeline.py`)
- [x] T018 [S0102] [P] Write unit tests for workspace lifecycle -- create, cleanup on success, partial preserve on failure, error codes registry coverage (`tests/test_workspace.py`)
- [x] T019 [S0102] Write tests for concurrent workspace isolation -- multiple simultaneous renders get independent directories and do not corrupt each other (`tests/test_workspace_isolation.py`)
- [x] T020 [S0102] Run full test suite, verify all tests passing, validate ASCII encoding and Unix LF line endings on all new/modified files

---

## Completion Checklist

Before marking session complete:

- [x] All tasks marked `[x]`
- [x] All tests passing (264 total: 235 original + 29 new)
- [x] All files ASCII-encoded
- [x] implementation-notes.md updated
- [x] Ready for the validate workflow step

---

## Next Steps

Run the validate workflow step to verify session completeness.
