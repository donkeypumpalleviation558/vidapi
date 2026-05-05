# Session 03: Progress Tracking and Cancellation

**Session ID**: `phase01-session03-progress-tracking-and-cancellation`
**Status**: Not Started
**Estimated Tasks**: ~20
**Estimated Duration**: 2-4 hours

---

## Objective

Add render progress reporting by parsing FFmpeg/Editly subprocess output, implement job cancellation for queued and running jobs, and add the GET /v1/renders list endpoint with pagination.

---

## Scope

### In Scope (MVP)
- Parse FFmpeg stderr for progress percentage (time-based)
- Parse Editly stdout/stderr for progress where available
- Update render progress field in DB during rendering
- Best-effort progress (never fail a render on parse errors)
- GET /v1/renders list endpoint with offset/limit pagination
- Filter renders by status (optional query param)
- DELETE /v1/renders/{id} for queued jobs (immediate cancel)
- DELETE /v1/renders/{id} for running jobs (best-effort via signal)
- Cancel status transition: queued -> cancelled
- Tests for progress parsing, list endpoint, and cancellation

### Out of Scope
- Multi-track compositing (session 04)
- Docker Compose (session 05)
- Cursor-based pagination (keep offset/limit for MVP)

---

## Prerequisites

- [ ] Session 02 complete (worker pipeline with full state machine)

---

## Deliverables

1. FFmpeg progress parser module
2. Editly output progress parser
3. Progress update integration in worker render loop
4. GET /v1/renders list endpoint with pagination
5. DELETE /v1/renders/{id} cancellation endpoint
6. Tests for parsers, list endpoint, and cancel flows

---

## Success Criteria

- [ ] Progress field updates during rendering (0-100 integer)
- [ ] GET /v1/renders returns paginated list of render jobs
- [ ] DELETE /v1/renders/{id} cancels queued jobs immediately
- [ ] DELETE /v1/renders/{id} sends signal to running renders (best-effort)
- [ ] Cancelled renders transition to "cancelled" status
- [ ] Progress parse errors do not fail the render
