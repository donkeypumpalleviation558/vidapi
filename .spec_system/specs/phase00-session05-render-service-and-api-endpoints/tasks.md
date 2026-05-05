# Task Checklist

**Session ID**: `phase00-session05-render-service-and-api-endpoints`
**Total Tasks**: 20
**Estimated Duration**: 3-4 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0005]` = Session reference (Phase 00, Session 05)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 2 | 2 | 0 |
| Foundation | 5 | 5 | 0 |
| Implementation | 8 | 8 | 0 |
| Testing | 5 | 5 | 0 |
| **Total** | **20** | **20** | **0** |

---

## Setup (2 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0005] Verify prerequisites met -- confirm sessions 01-04 outputs exist (composition models, DB model, asset service, renderer, poster), tools available (Python, FFmpeg)
- [x] T002 [S0005] Create file stubs for session deliverables (`app/services/render_service.py`, `app/db/render_crud.py`, `app/services/merge.py`, `app/api/routes_renders.py`, `tests/test_api_renders.py`, `tests/fixtures/sample_composition.json`)

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T003 [S0005] Add async DB session dependency to `app/api/deps.py` and wire table creation into app lifespan in `app/main.py` with cleanup on scope exit for the DB engine
- [x] T004 [S0005] [P] Create render CRUD operations module (`app/db/render_crud.py`) -- create_render, get_render_by_id, update_render_status, update_render_paths with idempotency protection and transaction boundaries
- [x] T005 [S0005] [P] Create merge variable expansion service (`app/services/merge.py`) -- walk composition JSON string fields and substitute `{{var}}` placeholders with schema-validated input and explicit error mapping for missing/invalid variables
- [x] T006 [S0005] Implement render service pipeline skeleton (`app/services/render_service.py`) -- define RenderService class with execute_render() entry point that the async worker will reuse, with cleanup on scope exit for workspace resources
- [x] T007 [S0005] Add render service, renderer, and DB session dependencies to `app/api/deps.py`

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T008 [S0005] Implement render service stage 1: validate composition, apply merge variables, persist input.json and expanded.json artifacts with idempotency protection, transaction boundaries, and compensation on failure
- [x] T009 [S0005] Implement render service stage 2: resolve all assets via AssetService, compile via EditlyRenderer with timeout, retry/backoff, and failure-path handling for the renderer subprocess
- [x] T010 [S0005] Implement render service stage 3: invoke EditlyRenderer.render, generate poster via generate_poster, persist output.mp4/poster.jpg/logs.txt, mark succeeded with duplicate-trigger prevention while in-flight
- [x] T011 [S0005] Implement render service failure handling: catch errors at each stage, persist partial artifacts (input.json, compiled spec when available, logs, replay metadata), transition to failed status with state reset on re-entry
- [x] T012 [S0005] Implement POST /v1/renders route handler (`app/api/routes_renders.py`) -- accept Composition body, call render service, return 202 with CreateRenderResponse, with schema-validated input and explicit error mapping
- [x] T013 [S0005] Implement GET /v1/renders/{id} route handler -- query DB, return RenderResponse with all fields (status, progress, url, poster, timestamps, error), with explicit loading, empty, error states
- [x] T014 [S0005] Implement GET /v1/renders/{id}/download route handler -- stream rendered output file via FileResponse, return 404 for unknown/incomplete/failed renders, with explicit error states
- [x] T015 [S0005] Create routes_renders.py router and wire into `app/main.py` under /v1 prefix

---

## Testing (5 tasks)

Verification and quality assurance.

- [x] T016 [S0005] [P] Create sample composition JSON test fixture (`tests/fixtures/sample_composition.json`) and update test conftest with DB setup, test storage, and render service fixtures
- [x] T017 [S0005] [P] Write API contract tests for POST /v1/renders -- valid composition returns 202 with render ID, invalid composition returns 422, missing required fields returns 422 (`tests/test_api_renders.py`)
- [x] T018 [S0005] [P] Write API contract tests for GET /v1/renders/{id} (404 for unknown ID, status fields present) and GET /v1/renders/{id}/download (404 for unknown/incomplete renders) (`tests/test_api_renders.py`)
- [x] T019 [S0005] Write golden-path end-to-end integration test: submit composition with image background + text overlay -> render succeeds -> poll returns succeeded -> download returns MP4 -> verify all 7 artifact files present (`tests/test_api_renders.py`)
- [x] T020 [S0005] Run full test suite and verify all tests pass, validate ASCII encoding on all session files

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
