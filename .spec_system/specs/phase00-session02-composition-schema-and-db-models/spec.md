# Session Specification

**Session ID**: `phase00-session02-composition-schema-and-db-models`
**Phase**: 00 - Foundation
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session defines the VidAPI JSON composition schema using Pydantic v2 discriminated unions and implements the render database model with SQLite persistence. These models form the contract that every subsequent session depends on: the composition schema defines what clients submit, and the render model defines how VidAPI tracks job lifecycle.

The composition schema must be renderer-independent -- it represents VidAPI's own timeline vocabulary (timeline, tracks, clips, assets, output settings) and will later be compiled into renderer-specific specs by sessions 04 and beyond. The render DB model implements the job status state machine defined in the PRD and stores all the metadata fields needed for status polling, artifact retrieval, and error diagnostics.

This is a pure data-modeling session. No HTTP routes, no rendering logic, no asset fetching. The deliverables are Pydantic models, SQLModel database models, Alembic migration infrastructure, and comprehensive validation tests.

---

## 2. Objectives

1. Define Pydantic v2 composition models covering all MVP asset types (video, image, text, audio, color) with discriminated unions
2. Implement the Output model with resolution presets, aspect ratio logic, quality-to-CRF mapping, and dimension validation
3. Create the Render SQLModel database model with full state machine fields, timestamps, and artifact path columns
4. Set up Alembic migration infrastructure with an initial migration for the renders table
5. Build comprehensive schema validation tests covering valid compositions, invalid inputs, edge cases, and resolution preset resolution

---

## 3. Prerequisites

### Required Sessions
- [x] `phase00-session01-project-skeleton-and-config` - Project skeleton, FastAPI app, config, health endpoint

### Required Tools/Knowledge
- Pydantic v2 discriminated unions and model validators
- SQLModel async patterns with aiosqlite
- Alembic migration configuration

### Environment Requirements
- Python 3.11+ virtual environment with project dependencies installed
- SQLite available (bundled with Python)

---

## 4. Scope

### In Scope (MVP)
- Composition model with timeline, output, merge, callback, and renderer fields
- Timeline model with background color, tracks list, and optional soundtrack
- Track model with clips list
- Clip model with asset, start, length, fit, position, offset, scale, opacity, transition, transform
- Asset discriminated union: VideoAsset, ImageAsset, TextAsset, AudioAsset, ColorAsset
- Position model supporting named positions and normalized coordinates
- Offset model for relative x/y adjustments
- Transition model with name and duration
- Output model with format, explicit dimensions, resolution presets, aspect ratio, fps, quality
- Resolution preset resolution to concrete width/height pairs per aspect ratio
- H.264 quality-to-CRF/preset mapping
- RenderStatus enum matching the PRD state machine with transition validation
- Render SQLModel with id, status, progress, stage, renderer, input/expanded/compiled/output/poster/replay/log paths, error fields, timestamps
- SQLite async session factory
- Alembic configuration and initial migration
- Render request/response Pydantic models (for later use by API routes)
- Schema validation tests for valid and invalid compositions

### Out of Scope (Deferred)
- HTML asset type - *Reason: deferred to Phase 04 HyperFrames renderer*
- Asset fetching and resolution - *Reason: Session 03 scope*
- Storage adapter implementation - *Reason: Session 03 scope*
- Renderer protocol and implementation - *Reason: Session 04 scope*
- API route handlers - *Reason: Session 05 scope*
- Template models - *Reason: Phase 02 scope*
- Webhook models - *Reason: Phase 02 scope*

---

## 5. Technical Approach

### Architecture
Pure data layer: Pydantic models define the public-facing JSON schema; SQLModel defines the persistence schema. The composition models validate incoming JSON but do not perform any rendering or asset resolution. The render model tracks job lifecycle with explicit status transitions.

### Design Patterns
- **Discriminated Union**: Asset types use Pydantic v2 discriminated unions on `type` field for clean polymorphism
- **Value Object**: Position, Offset, Transition, Transform are immutable value objects
- **State Machine**: RenderStatus enum with explicit allowed transitions method
- **Repository Pattern**: Session factory returns async sessions; queries go through SQLModel select()

### Technology Stack
- Pydantic v2 (2.11.2) - Schema validation and discriminated unions
- SQLModel (0.0.24) - Database models bridging Pydantic and SQLAlchemy
- aiosqlite (0.21.0) - Async SQLite driver
- Alembic - Database migration management
- pytest + pytest-asyncio - Testing

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/models/composition.py` | Pydantic v2 composition, timeline, track, clip, asset models | ~350 |
| `app/models/render.py` | Render request/response Pydantic models and RenderStatus enum | ~120 |
| `app/db/models.py` | SQLModel Render database model | ~80 |
| `app/db/session.py` | Async SQLite session factory | ~40 |
| `alembic.ini` | Alembic configuration | ~30 |
| `alembic/env.py` | Alembic environment with async support | ~60 |
| `alembic/script.mako` | Alembic migration template | ~25 |
| `alembic/versions/001_initial_renders.py` | Initial migration for renders table | ~50 |
| `tests/test_composition_schema.py` | Composition schema validation tests | ~250 |
| `tests/test_render_model.py` | Render model and status transition tests | ~100 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/models/__init__.py` | Re-export key models | ~10 |
| `app/db/__init__.py` | Re-export session factory | ~5 |
| `pyproject.toml` | Add alembic dependency | ~2 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Valid VidAPI JSON compositions parse without errors through Pydantic models
- [ ] Invalid compositions (missing fields, bad types, unknown asset types) raise ValidationError
- [ ] All five MVP asset types (video, image, text, audio, color) discriminate correctly on `type` field
- [ ] Resolution presets resolve to correct width/height for all aspect ratio combinations
- [ ] Quality presets map to correct CRF and FFmpeg preset values
- [ ] Output model validates dimension constraints (max width/height from config)
- [ ] Render records can be created, read, and updated in SQLite
- [ ] RenderStatus enum enforces valid state transitions
- [ ] Render model stores all artifact paths and error fields defined in PRD

### Testing Requirements
- [ ] Unit tests for all composition model variants
- [ ] Unit tests for resolution preset resolution
- [ ] Unit tests for render status transitions (valid and invalid)
- [ ] Unit tests for render DB model CRUD
- [ ] Alembic migration applies and rolls back cleanly

### Non-Functional Requirements
- [ ] All models use Pydantic v2 syntax (not v1 compat)
- [ ] Composition schema is renderer-independent

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (snake_case, type hints, etc.)
- [ ] ruff check passes
- [ ] mypy passes (strict mode)

---

## 8. Implementation Notes

### Key Considerations
- The `type` field on assets must be a string literal for Pydantic v2 discriminated unions to work properly
- Position model needs to support both named positions ("center", "top", "bottom-left", etc.) and normalized coordinate pairs
- Start and length on clips are in absolute seconds (not relative) -- this is what the segment compiler will convert later
- Render IDs should use ULID-style sortable format with `render_` prefix as specified in PRD
- SQLModel requires careful handling of optional fields vs nullable columns

### Potential Challenges
- **Discriminated unions with optional fields**: Pydantic v2 requires the discriminator field to be present on all union members; ensure each asset subclass has `type` as a literal
- **Resolution preset + explicit dimensions**: Need clear precedence rules -- explicit width/height wins per PRD
- **Alembic with async**: Alembic async support requires special env.py configuration with `run_async`
- **SQLModel + Alembic compatibility**: SQLModel metadata must be imported in Alembic env.py for auto-generation

### Relevant Considerations
- [Architecture] Text rendering via Pillow has limited typography compared to browser-based rendering -- ensure TextAsset model captures all needed styling fields for Pillow rendering in Session 03
- [External Dependencies] FFmpeg 6+ needed for later sessions -- no impact on this session's pure data modeling
- [What to Avoid] Avoid leaking renderer-specific details into composition models -- keep the schema VidAPI-owned

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Schema validation must reject malformed input with clear error messages, not silently coerce
- Resolution preset logic must handle all documented aspect ratio + resolution combinations without gaps
- RenderStatus transitions must be enforced -- invalid transitions should raise explicit errors, not silently succeed

---

## 9. Testing Strategy

### Unit Tests
- Test each asset type parses correctly from JSON dict
- Test discriminated union selects correct asset class based on `type` field
- Test unknown asset type raises ValidationError
- Test clip with all optional fields populated
- Test clip with minimal required fields only
- Test composition with all supported asset types
- Test output resolution presets for each aspect ratio (16:9, 9:16, 1:1, 4:5) and resolution (360, 480, 720, 1080, 4k)
- Test explicit width/height overrides resolution preset
- Test quality maps to correct CRF and FFmpeg preset
- Test RenderStatus valid transitions succeed
- Test RenderStatus invalid transitions raise error
- Test Render model CRUD (create, read, update status)

### Integration Tests
- Test Alembic migration upgrade and downgrade
- Test Render model persistence through async SQLite session

### Manual Testing
- Parse the example JSON composition from the PRD through the model
- Verify Alembic migration creates expected table schema

### Edge Cases
- Zero-length clip rejection
- Negative start time rejection
- Opacity outside 0.0-1.0 range
- Scale <= 0 rejection
- FPS outside valid range
- Empty tracks list
- Empty clips list in a track
- Missing required asset fields per type

---

## 10. Dependencies

### External Libraries
- pydantic: 2.11.2 (already installed)
- sqlmodel: 0.0.24 (already installed)
- aiosqlite: 0.21.0 (already installed)
- alembic: latest (to be added)

### Other Sessions
- **Depends on**: phase00-session01-project-skeleton-and-config
- **Depended by**: phase00-session03-storage-and-asset-service, phase00-session04-editly-renderer-and-segment-compiler, phase00-session05-render-service-and-api-endpoints

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
