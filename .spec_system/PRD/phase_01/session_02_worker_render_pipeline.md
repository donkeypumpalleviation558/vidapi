# Session 02: Worker Render Pipeline

**Session ID**: `phase01-session02-worker-render-pipeline`
**Status**: Not Started
**Estimated Tasks**: ~20
**Estimated Duration**: 2-4 hours

---

## Objective

Implement the full render worker pipeline with proper status transitions through the complete state machine, isolated per-job workspaces, structured log capture, and robust error handling.

---

## Scope

### In Scope (MVP)
- Full status state machine: queued -> fetching -> compiling -> rendering -> uploading -> succeeded/failed
- Worker updates status at each pipeline stage
- Per-job workspace isolation (unique directory per render)
- Workspace cleanup after artifacts are persisted to storage
- Structured log capture per render (logs.txt artifact)
- Error normalization with stable error codes
- Graceful handling of subprocess timeouts
- Worker retry/failure semantics for ARQ
- Status timestamp tracking (started_at, completed_at)
- Tests for status transitions and workspace isolation

### Out of Scope
- Progress percentage parsing (session 03)
- Job cancellation (session 03)
- Multi-track compositing changes (session 04)

---

## Prerequisites

- [ ] Session 01 complete (ARQ queue integration working)

---

## Deliverables

1. Worker pipeline with full status state machine transitions
2. Per-job workspace isolation implementation
3. Workspace cleanup lifecycle management
4. Structured render log capture as artifact
5. Error normalization with machine-readable codes
6. Tests for state transitions and workspace isolation

---

## Success Criteria

- [ ] Worker transitions through queued -> fetching -> compiling -> rendering -> uploading -> succeeded
- [ ] Failed renders transition to "failed" with normalized error code and message
- [ ] Each render job gets its own isolated workspace directory
- [ ] Workspaces are cleaned up after artifacts are persisted
- [ ] Render logs are captured and stored as logs.txt artifact
- [ ] Concurrent jobs do not corrupt each other's workspaces
