# Session Specification

**Session ID**: `phase01-session01-redis-arq-queue-integration`
**Phase**: 01 - Async Jobs and Multi-track
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session integrates Redis and ARQ into VidAPI so that render job execution is decoupled from the API request path. Currently, POST /v1/renders blocks while the full render pipeline executes synchronously inside the request handler. After this session, the endpoint will enqueue a job to Redis via ARQ and return 202 Accepted immediately with a render ID.

A minimal worker skeleton will be implemented that dequeues jobs from Redis, invokes the existing RenderService.execute_render() pipeline, and updates render status in the database upon completion or failure. This is the foundational session for the entire Phase 01 async architecture -- all subsequent sessions (worker pipeline enrichment, progress tracking, cancellation, multi-track, Docker Compose) build on the queue integration established here.

The session preserves backward compatibility by introducing a RENDER_MODE setting: "async" mode enqueues via ARQ (production default), while "sync" mode retains the current inline behavior for local development and testing without Redis.

---

## 2. Objectives

1. Add ARQ and Redis dependencies to the project
2. Create Redis connection configuration with environment-based URL
3. Implement ARQ worker module that dequeues and processes render jobs
4. Modify POST /v1/renders to enqueue via ARQ and return 202 immediately
5. Provide sync/async render mode toggle for backward-compatible testing

---

## 3. Prerequisites

### Required Sessions
- [x] `phase00-session01-project-skeleton-and-config` - FastAPI skeleton, config, logging
- [x] `phase00-session02-composition-schema-and-db-models` - Pydantic models, DB schema
- [x] `phase00-session03-storage-and-asset-service` - Storage adapter, asset resolution
- [x] `phase00-session04-editly-renderer-and-segment-compiler` - Renderer, compiler
- [x] `phase00-session05-render-service-and-api-endpoints` - RenderService, API endpoints

### Required Tools/Knowledge
- Redis 7+ available locally (Docker or system install)
- ARQ library concepts (async Redis queue, worker class)

### Environment Requirements
- Redis instance accessible at configurable URL (default: redis://localhost:6379)
- Python 3.11+ with async support

---

## 4. Scope

### In Scope (MVP)
- Add `arq` and `redis` Python packages as dependencies
- Redis URL configuration via REDIS_URL environment variable
- ARQ connection pool settings and lifecycle management
- Worker settings module with task registration
- Render worker task function that calls RenderService.execute_render()
- POST /v1/renders conditionally enqueues (async) or executes inline (sync)
- RENDER_MODE setting to toggle between "async" and "sync" modes
- Worker updates render status to queued on enqueue, delegates rest to RenderService
- Basic integration of ARQ health info into /v1/health endpoint
- Unit tests for the enqueue path (mocked Redis)
- Unit tests for the worker task function

### Out of Scope (Deferred)
- Full granular status state machine (fetching/compiling/rendering/uploading) - *Reason: Session 02*
- Progress percentage tracking from FFmpeg/Editly output - *Reason: Session 03*
- Job cancellation (DELETE endpoint) - *Reason: Session 03*
- GET /v1/renders list endpoint with pagination - *Reason: Session 03*
- Docker Compose with Redis service - *Reason: Session 05*
- Multi-track z-order changes - *Reason: Session 04*
- Workspace isolation for concurrent jobs - *Reason: Session 02*
- Rate limiting on POST /v1/renders - *Reason: Session 03*

---

## 5. Technical Approach

### Architecture
The API process and worker process share the same database and storage adapters. ARQ connects them through Redis:

```
Client -> POST /v1/renders -> FastAPI (validate, create DB record, enqueue) -> 202
                                                     |
                                                     v
                                              Redis (ARQ queue)
                                                     |
                                                     v
                                              Worker (dequeue, execute_render, update DB)
```

### Design Patterns
- **Strategy pattern**: RENDER_MODE selects inline vs enqueue execution path
- **Existing service reuse**: Worker calls RenderService.execute_render() unchanged
- **Graceful degradation**: Sync mode allows full test suite to run without Redis

### Technology Stack
- ARQ >= 0.26 (async Redis queue library)
- redis[hiredis] >= 5.0 (Redis client with C parser)
- Redis 7+ (message broker)

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/workers/render_worker.py` | ARQ worker task and settings | ~80 |
| `app/workers/arq_settings.py` | ARQ WorkerSettings class for CLI startup | ~30 |
| `app/core/redis.py` | Redis connection pool management | ~50 |
| `tests/test_worker_enqueue.py` | Tests for enqueue and worker task | ~120 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `pyproject.toml` | Add arq, redis dependencies | ~5 |
| `app/core/config.py` | Add REDIS_URL, RENDER_MODE settings | ~10 |
| `app/api/routes_renders.py` | Conditional enqueue vs sync render | ~30 |
| `app/api/deps.py` | Add ARQ pool dependency | ~15 |
| `app/main.py` | Redis pool lifecycle in lifespan | ~15 |
| `app/api/routes_health.py` | Optional Redis health info | ~15 |
| `app/models/render.py` | Ensure QUEUED status exists | ~5 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] POST /v1/renders returns 202 Accepted with status "queued" when RENDER_MODE=async
- [ ] Worker dequeues job from Redis and invokes render pipeline
- [ ] Worker updates DB render status to succeeded or failed on completion
- [ ] POST /v1/renders still works synchronously when RENDER_MODE=sync
- [ ] Worker process can start independently via `arq app.workers.arq_settings.WorkerSettings`
- [ ] Health endpoint reports Redis connectivity when async mode is active

### Testing Requirements
- [ ] Unit tests for enqueue path pass with mocked Redis
- [ ] Unit tests for worker task function pass
- [ ] Existing render API tests pass unchanged (sync mode)
- [ ] No import errors when Redis is unavailable in sync mode

### Non-Functional Requirements
- [ ] POST /v1/renders responds in < 200ms when enqueuing (no render blocking)
- [ ] Worker connects to Redis within 5 seconds or fails with clear error

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (ruff, type hints)

---

## 8. Implementation Notes

### Key Considerations
- RenderService.execute_render() already manages the full pipeline lifecycle including DB status updates -- the worker task is a thin wrapper
- The existing route already returns 202 status code, so the response contract is unchanged
- ARQ serializes job arguments as msgpack; only pass render_id (string) to avoid serialization issues with Pydantic models

### Potential Challenges
- **DB session in worker context**: Worker needs its own async session factory, not the FastAPI dependency injection. Mitigation: import get_session_factory() directly
- **ARQ connection lifecycle**: Pool must be created on worker startup and closed on shutdown. Mitigation: use ARQ's built-in on_startup/on_shutdown hooks
- **Test isolation**: Tests must work without Redis. Mitigation: RENDER_MODE=sync bypasses all ARQ code paths

### Relevant Considerations
- [P00] **Synchronous render in POST handler**: This session directly eliminates this tech debt
- [P00] **No rate limiting on POST /v1/renders**: Acknowledged but deferred to Session 03
- [P00] **Lazy engine init with set_engine()**: Worker must initialize its own DB engine on startup

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- POST /v1/renders must not silently drop jobs if Redis is unreachable (fail fast with 503)
- Worker must not leave render records in non-terminal state if task crashes (cleanup on failure)
- Health check must not block or timeout if Redis is slow (bounded timeout on ping)

---

## 9. Testing Strategy

### Unit Tests
- Enqueue function called with correct render_id when RENDER_MODE=async
- Worker task retrieves render_id, builds dependencies, calls execute_render
- Worker task handles RenderServiceError and marks render as failed
- Sync mode bypasses enqueue entirely

### Integration Tests
- Worker processes a real render job end-to-end (requires Redis)
- Marked with pytest.mark.integration for selective running

### Manual Testing
- Start Redis via Docker
- Start worker: `arq app.workers.arq_settings.WorkerSettings`
- POST a composition and verify 202 response
- Verify worker picks up job (stdout logs)
- GET /v1/renders/{id} shows succeeded status

### Edge Cases
- Redis unavailable at enqueue time: return 503 Service Unavailable
- Worker crashes mid-render: render stays in non-terminal state (acceptable for now, session 02 adds recovery)
- Worker starts before any jobs exist: idles cleanly
- Multiple simultaneous enqueues: each gets unique job ID

---

## 10. Dependencies

### External Libraries
- arq: >= 0.26
- redis[hiredis]: >= 5.0

### Other Sessions
- **Depends on**: All Phase 00 sessions (complete)
- **Depended by**: phase01-session02 (worker pipeline), phase01-session03 (cancellation), phase01-session05 (Docker Compose)

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
