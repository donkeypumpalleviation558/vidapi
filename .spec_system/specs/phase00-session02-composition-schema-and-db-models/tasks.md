# Task Checklist

**Session ID**: `phase00-session02-composition-schema-and-db-models`
**Total Tasks**: 20
**Estimated Duration**: 2.5-3.5 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0002]` = Session reference (Phase 00, Session 02)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 2 | 2 | 0 |
| Foundation | 6 | 6 | 0 |
| Implementation | 8 | 8 | 0 |
| Testing | 4 | 4 | 0 |
| **Total** | **20** | **20** | **0** |

---

## Setup (2 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0002] Verify prerequisites met: Python 3.11+ venv active, session 01 artifacts exist, pydantic/sqlmodel/aiosqlite installed (`app/core/config.py`, `pyproject.toml`)
- [x] T002 [S0002] Add alembic dependency to pyproject.toml and install it (`pyproject.toml`)

---

## Foundation (6 tasks)

Core types, enums, and base models.

- [x] T003 [S0002] [P] Define asset base and discriminated union types: VideoAsset, ImageAsset, TextAsset, AudioAsset, ColorAsset with type literal discriminator (`app/models/composition.py`)
- [x] T004 [S0002] [P] Define value objects: Position (named positions + normalized coords), Offset (x/y adjustment), Transition (name + duration), Transform (rotation/skew placeholder) (`app/models/composition.py`)
- [x] T005 [S0002] [P] Define RenderStatus enum with all 8 status values and an allowed_transitions method that enforces the PRD state machine (`app/models/render.py`)
- [x] T006 [S0002] Define Clip model with asset (discriminated union), start, length, fit, position, offset, scale, opacity, transition, transform -- with validators for non-negative start, positive length, opacity 0-1, scale > 0 (`app/models/composition.py`)
- [x] T007 [S0002] Define Track and Timeline models: Track wraps a clips list, Timeline has background color, tracks list, and optional soundtrack AudioAsset (`app/models/composition.py`)
- [x] T008 [S0002] Define Output model with format enum, explicit width/height, resolution preset, aspect_ratio, fps, quality, resolution preset resolver that maps (resolution + aspect_ratio) to concrete dimensions, and quality-to-CRF/preset mapping (`app/models/composition.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T009 [S0002] Define top-level Composition model with timeline, output, merge (optional dict), callback (optional URL), and renderer selector; add model-level validator ensuring at least one track with at least one clip (`app/models/composition.py`)
- [x] T010 [S0002] Define render request/response Pydantic models: CreateRenderRequest wrapping Composition, RenderResponse with id/status/progress/urls/timestamps/error fields, CreateRenderResponse with id/status/created_at (`app/models/render.py`)
- [x] T011 [S0002] Create SQLModel Render database model with ULID-prefixed id, status, progress, stage, renderer, input/expanded/compiled/output/poster/replay/log paths, error_code, error_message, created_at, updated_at, started_at, completed_at (`app/db/models.py`)
- [x] T012 [S0002] Create async SQLite session factory with create_engine and async_sessionmaker, including table creation utility (`app/db/session.py`)
- [x] T013 [S0002] Configure Alembic: create alembic.ini with async SQLite URL and alembic/env.py with run_async and SQLModel metadata import (`alembic.ini`, `alembic/env.py`)
- [x] T014 [S0002] Create Alembic migration template and initial migration for the renders table with upgrade and downgrade (`alembic/script.mako`, `alembic/versions/001_initial_renders.py`)
- [x] T015 [S0002] Update app/models/__init__.py to re-export Composition, Asset types, Output, RenderStatus, and render request/response models (`app/models/__init__.py`)
- [x] T016 [S0002] Update app/db/__init__.py to re-export session factory and Render model (`app/db/__init__.py`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T017 [S0002] [P] Write composition schema validation tests: valid compositions with each asset type, discriminated union dispatch, minimal clip, full clip, resolution presets for all aspect ratios, quality mapping, invalid compositions (bad type, missing fields, zero length, negative start, opacity out of range) (`tests/test_composition_schema.py`)
- [x] T018 [S0002] [P] Write render model tests: RenderStatus valid transitions, RenderStatus invalid transitions raise error, Render DB model create/read/update through async session, ULID id generation (`tests/test_render_model.py`)
- [x] T019 [S0002] Run full test suite, ruff check, and mypy to verify all quality gates pass
- [x] T020 [S0002] Validate ASCII encoding on all created/modified files and verify Alembic migration applies and rolls back cleanly

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
