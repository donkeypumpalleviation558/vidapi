# Session Specification

**Session ID**: `phase01-session03-progress-tracking-and-cancellation`
**Phase**: 01 - Async Jobs and Multi-track
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session adds real-time render progress reporting and job cancellation to the VidAPI async worker pipeline. Progress is extracted by streaming FFmpeg/Editly subprocess stderr line-by-line and parsing time-based progress markers against the known total duration. Progress updates are written to the database at configurable intervals so clients polling GET /v1/renders/{id} see meaningful progress between 0 and 100.

Cancellation supports two paths: queued jobs transition immediately to CANCELLED via DELETE /v1/renders/{id}, while running jobs receive a best-effort cancellation signal -- the worker checks a cancel_requested_at flag between pipeline stages and kills the active subprocess if rendering is in progress.

This session also adds the GET /v1/renders list endpoint with offset/limit pagination and optional status filtering, completing the core render management API surface for Phase 01.

---

## 2. Objectives

1. Parse FFmpeg stderr output for time-based progress and update the render progress field (0-100) in real time during rendering
2. Implement DELETE /v1/renders/{id} to cancel queued jobs immediately and signal best-effort cancellation for running jobs
3. Implement GET /v1/renders list endpoint with offset/limit pagination and optional status filter
4. Ensure progress parse failures never cause a render to fail (best-effort parsing)

---

## 3. Prerequisites

### Required Sessions
- [x] `phase01-session01-redis-arq-queue-integration` - ARQ + Redis queue, async render path
- [x] `phase01-session02-worker-render-pipeline` - Stage-by-stage worker pipeline with external status transitions

### Required Tools/Knowledge
- FFmpeg stderr output format for progress parsing
- ARQ job lifecycle and abort mechanisms
- FastAPI query parameter validation

### Environment Requirements
- Python 3.12+ with project virtualenv
- Redis running for async mode testing
- FFmpeg 6+ and Node.js with Editly available

---

## 4. Scope

### In Scope (MVP)
- Worker can parse FFmpeg stderr for time-based progress percentage - progress parser module with line-by-line streaming
- Worker can update render progress field in DB during rendering - real-time progress callback at bounded intervals
- Worker can detect cancellation between pipeline stages - cancel_requested_at DB flag checked between stages
- Worker can kill a running Editly/FFmpeg subprocess when cancellation is detected - SIGTERM then SIGKILL
- Client can GET /v1/renders to list recent render jobs - offset/limit pagination with deterministic ordering
- Client can filter renders by status - optional query parameter
- Client can DELETE /v1/renders/{id} to cancel queued jobs immediately - QUEUED to CANCELLED transition
- Client can DELETE /v1/renders/{id} to best-effort cancel running jobs - flag + worker cooperation
- Progress parse errors do not fail the render - best-effort with logged warnings

### Out of Scope (Deferred)
- Multi-track compositing - *Reason: Session 04*
- Docker Compose stack - *Reason: Session 05*
- Cursor-based pagination - *Reason: Keep offset/limit for MVP simplicity*
- WebSocket or SSE progress streaming - *Reason: Polling is sufficient for MVP*
- ARQ abort_job() integration - *Reason: DB flag is simpler and renderer-agnostic*

---

## 5. Technical Approach

### Architecture

Progress parsing works by changing EditlyRenderer.render() from blocking proc.communicate() to streaming stderr line-by-line via proc.stderr.readline(). Each line is passed to a progress parser that extracts FFmpeg time= values and computes percentage against total duration. A callback fires on meaningful progress changes (>= 2% delta) to update the DB.

Cancellation uses a cooperative model: DELETE endpoint sets cancel_requested_at on the render record. The worker checks this flag (a) on job pickup, (b) between each pipeline stage, and (c) during the progress callback loop while rendering. On detection, QUEUED jobs transition directly to CANCELLED; active jobs have their subprocess killed and transition to CANCELLED.

The list endpoint uses standard offset/limit with ORDER BY created_at DESC for deterministic pagination.

### Design Patterns
- **Callback pattern**: Progress callback passed to renderer allows worker to update DB without renderer knowing about persistence
- **Cooperative cancellation**: DB flag checked at defined checkpoints rather than preemptive signals
- **Best-effort parsing**: Progress parser returns Optional[float]; None on parse failure, never raises

### Technology Stack
- Python 3.12 / FastAPI
- SQLModel + aiosqlite (dev DB)
- ARQ + Redis (async queue)
- asyncio.subprocess for streaming stderr
- re module for FFmpeg progress regex

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/services/ffmpeg_progress.py` | FFmpeg stderr progress parser with line-by-line extraction | ~80 |
| `tests/test_ffmpeg_progress.py` | Unit tests for progress parser edge cases | ~150 |
| `tests/test_render_list.py` | Tests for GET /v1/renders list endpoint | ~180 |
| `tests/test_cancellation.py` | Tests for DELETE cancel endpoint and worker cancel flows | ~200 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/db/models.py` | Add cancel_requested_at column | ~5 |
| `app/models/render.py` | Add CANCELLED transitions from active states, list/pagination models | ~40 |
| `app/models/error_codes.py` | Add RENDER_CANCELLED error code | ~3 |
| `app/db/render_crud.py` | Add list_renders, set_cancel_requested, update_render_progress functions | ~60 |
| `app/renderers/editly.py` | Refactor render() to stream stderr with progress callback | ~60 |
| `app/workers/render_worker.py` | Add cancellation checks, progress callback, pre-flight cancel check | ~80 |
| `app/api/routes_renders.py` | Add GET /v1/renders list and DELETE /v1/renders/{id} endpoints | ~80 |
| `app/core/config.py` | Add progress_update_interval_seconds setting | ~3 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Progress field updates during rendering (0-100 integer)
- [ ] GET /v1/renders returns paginated list of render jobs
- [ ] GET /v1/renders supports optional status filter query parameter
- [ ] DELETE /v1/renders/{id} cancels queued jobs immediately (QUEUED -> CANCELLED)
- [ ] DELETE /v1/renders/{id} sets cancel flag for running renders (best-effort)
- [ ] Cancelled renders transition to CANCELLED status
- [ ] Progress parse errors do not fail the render
- [ ] Worker skips cancelled renders on pickup

### Testing Requirements
- [ ] Unit tests for FFmpeg progress parser cover normal, edge, and error cases
- [ ] API tests for list endpoint cover pagination, filtering, and empty results
- [ ] API tests for cancel endpoint cover queued cancel, running cancel, not-found, and already-terminal
- [ ] All existing 264 tests continue to pass

### Non-Functional Requirements
- [ ] Progress updates are rate-limited (not more than once per 2 seconds by default)
- [ ] List endpoint responds under 200ms for typical result sets
- [ ] Cancel endpoint responds immediately without blocking on worker

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (CONVENTIONS.md)

---

## 8. Implementation Notes

### Key Considerations
- EditlyRenderer.render() currently uses proc.communicate() which buffers all stderr. Must change to line-by-line streaming to parse progress in real time.
- Progress percentage requires knowing total duration upfront -- compute from composition timeline in the worker before entering render stage.
- Cancel flag check must be cheap (single DB read) and not slow down the hot path.

### Potential Challenges
- **FFmpeg progress format variability**: FFmpeg stderr format varies across versions and modes. Use best-effort regex with graceful fallback. Mitigation: test with multiple known output formats, never fail on parse errors.
- **Race condition on cancel + complete**: Render might complete between cancel request and worker checking. Mitigation: only transition to CANCELLED if current state is not already terminal.
- **Subprocess kill cleanup**: Killing Editly may leave partial output files. Mitigation: workspace cleanup handles this; workspace_mgr.cleanup_failure removes orphaned files.

### Relevant Considerations
- [P00] **Synchronous render in POST handler**: This session focuses on the async path; sync path progress is not affected.
- [P00] **FFmpeg subprocess resource limits**: Progress parsing gives visibility into long-running renders, complementing future resource limit enforcement.
- [P00] **No render workspace cleanup**: Cancellation must trigger workspace cleanup for cancelled renders, leveraging existing WorkspaceManager.

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Progress callback writes to DB at unbounded rate without interval throttling
- Cancel endpoint allows duplicate cancellation requests without idempotent handling
- List endpoint returns unbounded results without pagination enforcement

---

## 9. Testing Strategy

### Unit Tests
- FFmpeg progress parser: normal time output, malformed lines, empty input, zero duration, 100% completion
- Progress percentage calculation: edge cases for very short and very long durations

### Integration Tests
- List endpoint: empty list, multiple renders, pagination (offset/limit), status filter, invalid status
- Cancel endpoint: cancel queued render, cancel running render, cancel non-existent, cancel already-terminal, idempotent cancel

### Manual Testing
- Submit a render in async mode, poll and observe progress incrementing
- Submit a render, cancel while queued, verify CANCELLED status
- Submit a render, wait for rendering stage, cancel, verify CANCELLED status

### Edge Cases
- Cancel request arrives after render completes (race condition)
- Progress parse produces NaN or > 100 (clamp to 0-100)
- Very fast render completes before first progress update
- List endpoint with zero renders
- List endpoint with offset beyond total count

---

## 10. Dependencies

### External Libraries
- No new dependencies required (uses existing asyncio, re, SQLModel, FastAPI)

### Other Sessions
- **Depends on**: phase01-session01 (ARQ queue), phase01-session02 (worker pipeline)
- **Depended by**: phase01-session04 (multi-track), phase01-session05 (Docker Compose)

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
