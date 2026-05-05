# Task Checklist

**Session ID**: `phase04-session01-renderer-capability-registry`
**Total Tasks**: 22
**Estimated Duration**: 3-4 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[SNNMM]` = Session reference (NN=phase number, MM=session number)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 3 | 3 | 0 |
| Foundation | 6 | 6 | 0 |
| Implementation | 9 | 9 | 0 |
| Testing | 4 | 4 | 0 |
| **Total** | **22** | **22** | **0** |

---

## Setup (3 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0401] Verify existing renderer, composition schema, API render, worker, metrics, and fixture behavior before changing validation (`app/renderers/__init__.py`)
- [x] T002 [S0401] [P] Confirm no Alembic migration is required because selected renderer metadata uses the existing render column (`app/db/models.py`)
- [x] T003 [S0401] [P] Create renderer capability documentation scaffold for selection semantics and support matrix (`docs/renderer-capabilities.md`)

---

## Foundation (6 tasks)

Core structures and base implementations.

- [x] T004 [S0401] Create typed renderer capability registry with immutable support declarations for assets, outputs, transitions, captions, poster options, and availability (`app/renderers/capabilities.py`)
- [x] T005 [S0401] Add stable renderer capability exception types and safe error context helpers with schema-validated input and explicit error mapping (`app/renderers/capabilities.py`)
- [x] T006 [S0401] Add unsupported renderer and unsupported renderer feature codes to the stable error-code catalog (`app/models/error_codes.py`)
- [x] T007 [S0401] Add documented API error response metadata for unsupported renderer and unsupported feature failures (`app/models/errors.py`)
- [x] T008 [S0401] Update renderer protocol and exports to expose capability-aware resolution without concrete Editly coupling (`app/renderers/base.py`)
- [x] T009 [S0401] Update renderer package resolver to select Editly for omitted or auto renderer and reject unavailable renderers deterministically (`app/renderers/__init__.py`)

---

## Implementation (9 tasks)

Main feature implementation.

- [x] T010 [S0401] Validate composition renderer compatibility before render limit and queue admission boundaries with schema-validated input and explicit error mapping (`app/api/routes_renders.py`)
- [x] T011 [S0401] Map renderer capability failures to stable redacted API envelopes with authorization behavior unchanged (`app/api/routes_renders.py`)
- [x] T012 [S0401] Update FastAPI dependencies and render service construction to use protocol or resolver-based renderer selection (`app/api/deps.py`)
- [x] T013 [S0401] Update render service compile path to validate selected renderer, persist renderer metadata before risky work, and prevent duplicate ambiguous compile failures while in-flight (`app/services/render_service.py`)
- [x] T014 [S0401] Update worker pipeline to revalidate queued compositions, persist selected renderer on failure, and map unsupported combinations before renderer invocation with explicit error mapping (`app/workers/render_worker.py`)
- [x] T015 [S0401] Update render CRUD helpers to support selected-renderer persistence through existing render metadata with deterministic failure-path handling (`app/db/render_crud.py`)
- [x] T016 [S0401] Align composition schema renderer and output fields with capability validation boundaries without changing existing default Editly behavior (`app/models/composition.py`)
- [x] T017 [S0401] Update structured renderer logs and metrics labels so selected renderer appears without raw payload, asset URL, callback URL, or secret leakage (`app/services/metrics.py`)
- [x] T018 [S0401] Update README and architecture docs with renderer protocol, capability registry, default Editly behavior, and future adapter extension points (`README.md`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T019 [S0401] [P] Write unit tests for capability registry lookup, auto/default selection, unavailable renderer names, unsupported outputs, and safe error context (`tests/test_renderer_capabilities.py`)
- [x] T020 [S0401] [P] Write API and service flow tests for default Editly, explicit Editly, invalid renderer, unsupported feature rejection, and selected renderer persistence (`tests/test_renderer_selection_flow.py`)
- [x] T021 [S0401] Update existing render, worker, metrics, and fixture tests for protocol-based renderer selection and redacted failure metadata (`tests/test_api_renders.py`)
- [x] T022 [S0401] Run targeted tests, linter/type checks where feasible, and ASCII validation on all session artifacts (`tests/test_renderer_capabilities.py`)

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
