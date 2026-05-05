# Session 01: Redis ARQ Queue Integration

**Session ID**: `phase01-session01-redis-arq-queue-integration`
**Status**: Not Started
**Estimated Tasks**: ~20
**Estimated Duration**: 2-4 hours

---

## Objective

Integrate Redis and ARQ into the application so that POST /v1/renders enqueues a job and returns 202 Accepted immediately, with a minimal worker skeleton that can dequeue and process jobs.

---

## Scope

### In Scope (MVP)
- Add ARQ and redis dependencies
- Create ARQ worker settings and connection pool configuration
- Create render worker task function skeleton
- Modify POST /v1/renders to enqueue job via ARQ instead of rendering synchronously
- Return 202 Accepted with render ID and status "queued"
- Worker dequeues job and invokes existing render service
- Worker updates render status on completion or failure
- Basic ARQ health check integration
- Configuration for Redis URL (env variable)
- Unit tests for enqueue path and worker task

### Out of Scope
- Full state machine (session 02)
- Progress tracking (session 03)
- Job cancellation (session 03)
- Docker Compose (session 05)
- Multi-track changes (session 04)

---

## Prerequisites

- [ ] Phase 00 complete (render service works synchronously)
- [ ] Redis available locally (docker run or system install)

---

## Deliverables

1. ARQ worker module (`app/workers/render_worker.py`)
2. ARQ settings/configuration
3. Modified POST /v1/renders returning 202
4. Redis connection configuration in app settings
5. Tests covering enqueue and basic worker flow

---

## Success Criteria

- [ ] POST /v1/renders returns 202 Accepted with status "queued"
- [ ] Worker picks up job from Redis queue
- [ ] Worker invokes render service and updates DB status
- [ ] Existing render tests still pass (backward compatible)
- [ ] Worker can be started independently from the API process
