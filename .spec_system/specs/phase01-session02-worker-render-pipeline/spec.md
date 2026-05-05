# Session Specification

**Session ID**: `phase01-session02-worker-render-pipeline`
**Phase**: 01 - Async Jobs and Multi-track
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session transforms the minimal ARQ worker skeleton from Session 01 into a robust render pipeline with explicit stage-by-stage status transitions, per-job workspace isolation, structured log capture, workspace cleanup, and normalized error codes.

Currently, the worker task is a thin wrapper that calls `RenderService.execute_render()` which internally creates a new render record and manages all status transitions. This creates a mismatch in async mode: the API route already creates the render record before enqueuing, but `execute_render()` creates a second one. Session 02 refactors the pipeline so the worker drives status transitions against the existing render record, calling individual stage methods rather than a monolithic `execute_render()`. This separation is essential for Session 03 (progress tracking, cancellation) and Session 04 (multi-track), which need fine-grained control over each pipeline phase.

The session also addresses the [P00] tech debt item "No render workspace cleanup" by implementing workspace lifecycle management that removes temporary working files after artifacts are persisted to storage.

---

## 2. Objectives

1. Refactor RenderService to expose individual stage methods that accept a render_id rather than creating their own record
2. Rewrite the worker pipeline to drive status transitions (queued -> fetching -> compiling -> rendering -> uploading -> succeeded/failed) at each stage
3. Implement workspace lifecycle management with cleanup after artifact persistence
4. Formalize error codes into a registry and normalize all failure paths
5. Add structured per-render log collection across all pipeline stages

---

## 3. Prerequisites

### Required Sessions
- [x] `phase00-session01-project-skeleton-and-config` - FastAPI skeleton, config, logging
- [x] `phase00-session02-composition-schema-and-db-models` - Pydantic models, DB schema
- [x] `phase00-session03-storage-and-asset-service` - Storage adapter, asset resolution
- [x] `phase00-session04-editly-renderer-and-segment-compiler` - Renderer, compiler
- [x] `phase00-session05-render-service-and-api-endpoints` - RenderService, API endpoints
- [x] `phase01-session01-redis-arq-queue-integration` - ARQ queue, worker skeleton

### Required Tools/Knowledge
- Redis 7+ available locally
- Existing test suite passing (235 tests)
- Understanding of ARQ worker lifecycle hooks

### Environment Requirements
- Redis instance accessible at configurable URL
- Python 3.11+ with async support

---

## 4. Scope

### In Scope (MVP)
- Worker drives status transitions through full state machine at each pipeline stage
- RenderService refactored to accept render_id and expose per-stage methods
- Per-job workspace isolation verified and tested for concurrent renders
- Workspace cleanup after artifacts are persisted to storage
- Structured per-render log collector that captures all pipeline stages as logs.txt
- Error codes registry with stable machine-readable codes for all failure modes
- ARQ retry/failure semantics configuration (max_tries, retry_delay)
- started_at tracked on FETCHING transition, completed_at on terminal state
- Sync render path updated for compatibility with refactored RenderService
- Tests for status transitions, workspace isolation, cleanup, and error normalization

### Out of Scope (Deferred)
- Progress percentage parsing from FFmpeg/Editly output - *Reason: Session 03*
- Job cancellation (DELETE endpoint) - *Reason: Session 03*
- GET /v1/renders list endpoint with pagination - *Reason: Session 03*
- Multi-track compositing changes - *Reason: Session 04*
- Docker Compose configuration - *Reason: Session 05*

---

## 5. Technical Approach

### Architecture
The worker becomes the pipeline orchestrator in async mode. Instead of calling a monolithic `execute_render()`, the worker calls individual stage methods on RenderService and manages status transitions between them:

```
Worker:
  1. Mark FETCHING, call stage_validate_and_expand()
  2. Mark COMPILING, call stage_resolve_and_compile()
  3. Mark RENDERING, call stage_render_and_store()
  4. Mark UPLOADING, finalize artifacts
  5. Mark SUCCEEDED
  Finally: cleanup workspace temp files
```

The sync path retains a convenience method that orchestrates all stages internally for backward compatibility.

### Design Patterns
- **Pipeline pattern**: Worker orchestrates sequential stages with explicit state transitions between each
- **Strategy pattern**: Sync vs async execution paths share the same stage methods
- **Registry pattern**: Error codes formalized in a central registry for consistent normalization
- **Context manager**: Workspace lifecycle managed with guaranteed cleanup

### Technology Stack
- ARQ >= 0.26 (async Redis queue)
- structlog (structured log capture per render)
- pathlib (workspace filesystem operations)
- asyncio (subprocess timeout, async I/O)

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/models/error_codes.py` | Error code registry with stable codes | ~60 |
| `app/workers/workspace.py` | Workspace lifecycle manager (create, cleanup) | ~80 |
| `app/workers/log_collector.py` | Per-render structured log collector | ~70 |
| `tests/test_worker_pipeline.py` | Worker pipeline status transition tests | ~200 |
| `tests/test_workspace.py` | Workspace lifecycle and cleanup tests | ~120 |
| `tests/test_workspace_isolation.py` | Concurrent workspace isolation tests | ~100 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/services/render_service.py` | Expose stage methods, accept render_id | ~80 |
| `app/workers/render_worker.py` | Rewrite pipeline with stage-by-stage transitions | ~100 |
| `app/workers/arq_settings.py` | ARQ retry/failure configuration | ~15 |
| `app/core/config.py` | Workspace cleanup settings | ~5 |
| `app/api/routes_renders.py` | Update sync path for refactored service | ~20 |
| `app/db/render_crud.py` | Minor timestamp tracking adjustments | ~10 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Worker transitions through queued -> fetching -> compiling -> rendering -> uploading -> succeeded
- [ ] Failed renders transition to "failed" with normalized error code and message
- [ ] Each render job gets its own isolated workspace directory
- [ ] Workspaces are cleaned up after artifacts are persisted
- [ ] Render logs are captured and stored as logs.txt artifact covering all stages
- [ ] Concurrent jobs do not corrupt each other's workspaces

### Testing Requirements
- [ ] Unit tests for worker pipeline status transitions
- [ ] Unit tests for workspace lifecycle and cleanup
- [ ] Unit tests for error code normalization
- [ ] Tests for concurrent workspace isolation
- [ ] Existing test suite continues to pass

### Non-Functional Requirements
- [ ] Worker handles subprocess timeouts gracefully without orphaning workspaces
- [ ] Error codes are stable machine-readable strings usable by client code
- [ ] Workspace cleanup does not delete artifacts needed for debugging failed renders

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (ruff format, type hints)

---

## 8. Implementation Notes

### Key Considerations
- RenderService.execute_render() currently creates its own render record -- in async mode, the record already exists from the route handler. The refactored stage methods must accept render_id to operate on the existing record.
- The sync render path must continue to work for tests and local dev without Redis. A convenience method wrapping all stages preserves backward compatibility.
- Workspace cleanup should preserve artifacts for failed renders to aid debugging (input.json, logs.txt, compiled spec when available).

### Potential Challenges
- **DB session scope across stages**: Each stage needs a session. Use separate session scopes per stage to avoid long-lived transactions.
- **Cleanup on crash**: If the worker crashes mid-render, cleanup may not run. Acceptable for now; a TTL-based cleanup job can be added later.
- **Test isolation**: Tests must work without Redis (sync mode). Worker pipeline tests mock the DB and RenderService stages.

### Relevant Considerations
- [P00] **Synchronous render in POST handler**: Session 01 eliminated this; Session 02 completes the worker pipeline
- [P00] **No render workspace cleanup**: This session directly addresses this tech debt
- [P00] **FFmpeg subprocess resource limits**: Worker enforces timeout via asyncio.wait_for; memory limits deferred to Docker
- [P00] **Replay metadata (replay.json)**: Stage methods continue to produce replay artifacts

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Worker must clean up workspace temp files on scope exit even when pipeline fails
- Worker must not leave renders in non-terminal state after any failure path
- Log collector must not lose entries if a stage raises before flush

---

## 9. Testing Strategy

### Unit Tests
- Worker pipeline transitions through all status stages in order
- Worker marks FAILED with correct error code on each failure type
- Workspace manager creates isolated directories and cleans up correctly
- Error codes map correctly from exception types
- Log collector captures entries from all stages and writes logs.txt

### Integration Tests
- Worker processes a real render job end-to-end (requires Redis, marked integration)
- Concurrent jobs produce independent workspace directories

### Manual Testing
- Start Redis and worker process
- Submit render via API, verify status transitions via polling
- Verify workspace is cleaned up after success
- Verify workspace is partially preserved after failure (input + logs retained)

### Edge Cases
- Worker task receives nonexistent render_id: early return
- Worker task receives already-terminal render: skip with warning
- Subprocess timeout mid-render: FAILED with RENDER_TIMEOUT code, workspace cleaned
- Workspace directory already exists from a previous attempt: recreated safely
- Storage write fails during artifact persistence: FAILED with STORAGE_ERROR code

---

## 10. Dependencies

### External Libraries
- arq: >= 0.26 (already installed)
- redis[hiredis]: >= 5.0 (already installed)
- structlog (already installed)

### Other Sessions
- **Depends on**: phase01-session01-redis-arq-queue-integration
- **Depended by**: phase01-session03-progress-tracking-and-cancellation, phase01-session04-multi-track-and-audio-mixing, phase01-session05-docker-compose-stack

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
