# Session Specification

**Session ID**: `phase00-session05-render-service-and-api-endpoints`
**Phase**: 00 - Foundation
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session wires together all Phase 00 deliverables into the core VidAPI loop: accept a JSON composition via POST, orchestrate the full render pipeline (validate, expand, resolve assets, compile, render, generate poster, store artifacts), and expose the three MVP API endpoints. It is the capstone session that proves the end-to-end JSON-to-video workflow locally.

The render service operates synchronously in the API process for Phase 00 -- the same service boundary the async ARQ worker will call in Phase 01. This keeps the architecture clean while avoiding queue infrastructure before it is needed. The POST endpoint returns 202 Accepted to match the contract shape clients will rely on when rendering becomes truly asynchronous.

After this session, a developer can POST a JSON composition with an image background, text overlay, optional music, and vertical MP4 output settings, then poll for status and download the rendered video and poster through the API.

---

## 2. Objectives

1. Implement a render service that orchestrates the full render pipeline (validate -> expand -> resolve assets -> compile -> render -> poster -> store artifacts -> update status).
2. Expose POST /v1/renders, GET /v1/renders/{id}, and GET /v1/renders/{id}/download endpoints with proper Pydantic request/response models and error handling.
3. Persist all 7 artifact files for successful renders (input.json, expanded.json, compiled.editly.json, replay.json, output.mp4, poster.jpg, logs.txt) and partial artifacts for failed renders.
4. Prove the end-to-end loop with a golden-path integration test that submits JSON, polls status, downloads output, and verifies all artifacts.

---

## 3. Prerequisites

### Required Sessions
- [x] `phase00-session01-project-skeleton-and-config` - FastAPI skeleton, config, logging, error handling
- [x] `phase00-session02-composition-schema-and-db-models` - Pydantic composition models, DB Render model, request/response models, status state machine
- [x] `phase00-session03-storage-and-asset-service` - LocalStorage adapter, AssetService (remote/file/text resolution), SSRF protection, ffprobe
- [x] `phase00-session04-editly-renderer-and-segment-compiler` - EditlyRenderer (compile + render), segment compiler, poster generation

### Required Tools/Knowledge
- Python 3.11+ with FastAPI, Pydantic v2, SQLModel, structlog
- FFmpeg and ffprobe on PATH (for poster generation and media validation)
- Node.js and Editly on PATH (for actual rendering -- tests may mock this)

### Environment Requirements
- SQLite database path writable (data/vidapi.db)
- Render workspace directory writable (data/renders/)
- Asset cache directory writable (data/assets/)

---

## 4. Scope

### In Scope (MVP)
- Render service orchestrating the full pipeline behind a service boundary the worker will reuse - single entry point for the entire render lifecycle
- DB CRUD operations for render records - create, get by ID, update status and artifact paths
- Simple merge variable expansion via string substitution on composition JSON
- POST /v1/renders accepting a Composition body, returning 202 with render ID - with schema-validated input and explicit error mapping
- GET /v1/renders/{id} returning full status with all fields - with explicit loading, empty, error states
- GET /v1/renders/{id}/download streaming the rendered output file - with 404 when not found or not yet complete
- Artifact persistence for both successful and failed renders - with compensation on failure
- DB table initialization on app startup
- Golden-path end-to-end integration test
- API contract tests for validation errors, 404s, and download edge cases

### Out of Scope (Deferred)
- Async queue processing - *Reason: Phase 01 (ARQ + Redis)*
- List renders endpoint (GET /v1/renders) - *Reason: Phase 01*
- Delete/cancel endpoint - *Reason: Phase 01*
- Template endpoints - *Reason: Phase 02*
- Authentication - *Reason: Phase 03*
- Webhook callbacks - *Reason: Phase 02*

---

## 5. Technical Approach

### Architecture
The render service is a stateless orchestrator that accepts a Composition, creates a DB record, and executes each pipeline stage in sequence: validate -> expand (merge variables) -> resolve assets -> compile (Editly) -> render (subprocess) -> poster -> store artifacts -> mark succeeded/failed. It catches errors at each stage and persists partial artifacts before marking the render as failed.

Routes are thin FastAPI handlers that validate input, call the render service or DB CRUD, and return Pydantic response models. The POST handler runs the render synchronously in-process for Phase 00 but returns 202 to preserve the async contract shape.

### Design Patterns
- **Service boundary**: Render service encapsulates the full pipeline -- routes never call renderers or storage directly
- **Repository pattern**: Render CRUD operations isolated in a dedicated module
- **Dependency injection**: FastAPI Depends() for DB session, render service, storage
- **Pipeline with compensation**: Each stage persists artifacts; failures capture partial state before transitioning to failed status

### Technology Stack
- FastAPI 0.115+ (route handlers, dependency injection)
- SQLModel + aiosqlite (async DB operations)
- Pydantic v2 (request/response validation)
- structlog (structured logging with render_id context)
- httpx (test client via ASGITransport)

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/services/render_service.py` | Render pipeline orchestrator | ~250 |
| `app/db/render_crud.py` | DB CRUD operations for renders | ~80 |
| `app/services/merge.py` | Merge variable string substitution | ~50 |
| `app/api/routes_renders.py` | POST, GET, download route handlers | ~120 |
| `tests/test_api_renders.py` | API contract and integration tests | ~250 |
| `tests/fixtures/sample_composition.json` | Golden-path test fixture | ~40 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/main.py` | Add DB init to lifespan, register render routes | ~10 |
| `app/api/deps.py` | Add DB session, render service, renderer dependencies | ~30 |
| `tests/conftest.py` | Add DB setup fixture, test storage fixture | ~40 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] POST /v1/renders accepts valid composition JSON and returns 202 with render ID
- [ ] POST /v1/renders returns 422 for invalid compositions
- [ ] GET /v1/renders/{id} returns render status with all expected fields
- [ ] GET /v1/renders/{id} returns 404 for unknown render IDs
- [ ] GET /v1/renders/{id}/download streams the rendered MP4
- [ ] GET /v1/renders/{id}/download returns 404 for unknown or incomplete renders
- [ ] Successful render stores all 7 artifact files (input.json, expanded.json, compiled.editly.json, replay.json, output.mp4, poster.jpg, logs.txt)
- [ ] Failed render stores input JSON, compiled spec when available, logs, and replay metadata
- [ ] Render service uses the same interface the async worker will call in Phase 01

### Testing Requirements
- [ ] API contract tests for POST validation errors (422)
- [ ] API contract tests for GET 404 responses
- [ ] Golden-path end-to-end test with artifact verification
- [ ] All existing tests still passing

### Non-Functional Requirements
- [ ] Non-render API endpoints respond in under 200ms
- [ ] Every render reaches exactly one terminal state (succeeded or failed)
- [ ] Structured logs include render_id in every log line during render execution

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (thin routes, business logic in services)

---

## 8. Implementation Notes

### Key Considerations
- The render service must be structured so the ARQ worker can call the same `execute_render()` method in Phase 01 without changes to the service itself
- The POST endpoint returns 202 even though the render completes synchronously -- this preserves the async API contract
- Merge variable expansion uses simple string substitution for now; Jinja2 sandbox comes in Phase 02 with templates
- The download endpoint must stream file content, not load entire video into memory

### Potential Challenges
- **Editly/FFmpeg not installed locally**: Tests that need actual rendering must be skippable or use mocked subprocess calls
- **DB session lifecycle in tests**: Tests need fresh DB per test to avoid state leakage -- use in-memory SQLite with table creation in fixtures
- **Large file streaming**: Download endpoint needs FileResponse or StreamingResponse to avoid loading full MP4 into memory

### Relevant Considerations
- **FFmpeg subprocess spawning needs resource limits**: Render service must pass explicit timeouts to the renderer and poster generator
- **Synchronous rendering in API process blocks the event loop**: Acceptable for Phase 00 development only; the service boundary ensures Phase 01 can move this to a worker without API changes

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Render service state mutation without idempotency protection (double-submit could create duplicate renders)
- Failed render that does not persist partial artifacts (input.json, logs) loses debugging context
- Download endpoint without proper error states when output does not exist yet or render failed
- DB status updates without proper transition validation (could skip states)

---

## 9. Testing Strategy

### Unit Tests
- Merge variable expansion: substitution, missing variables, no-op when merge is null
- Render CRUD: create record, get by ID, update status, update artifact paths

### Integration Tests
- POST /v1/renders with valid composition returns 202
- POST /v1/renders with invalid JSON returns 422
- GET /v1/renders/{id} with valid ID returns status
- GET /v1/renders/{id} with unknown ID returns 404
- GET /v1/renders/{id}/download with unknown ID returns 404

### Manual Testing
- Submit a real composition with a local test image and verify MP4 output
- Inspect stored artifacts in data/renders/{id}/

### Edge Cases
- POST with empty tracks (should fail validation)
- POST with zero-length clip (should fail validation)
- GET download before render completes
- GET download for failed render
- Composition with merge variables but null merge field

---

## 10. Dependencies

### External Libraries
- fastapi: 0.115+
- sqlmodel: 0.0.22+
- aiosqlite: 0.20+
- structlog: 24.1+
- httpx: 0.27+ (test client)
- pydantic: 2.9+

### Other Sessions
- **Depends on**: phase00-session01, phase00-session02, phase00-session03, phase00-session04
- **Depended by**: phase01-session* (async worker will call the same render service)

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
