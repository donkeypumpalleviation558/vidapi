# Session Specification

**Session ID**: `phase04-session01-renderer-capability-registry`
**Phase**: 04 - Advanced Rendering
**Status**: Completed
**Created**: 2026-05-05

---

## 1. Session Overview

This session starts Phase 04 by making renderer capabilities explicit and enforceable before VidAPI compiles or executes a render. Previous phases established the Editly render path, async workers, output artifact storage, production limits, authentication, and operational metrics. Phase 04 adds additional renderers and output features, so the service now needs a stable way to decide which renderer can handle a requested composition and to reject unsupported combinations with predictable errors.

The work preserves Editly as the default behavior for requests that omit `renderer` or use `auto`. It formalizes support declarations for assets, output formats, transitions, captions, poster controls, and future renderer names, then wires validation into API and worker paths so invalid combinations fail before job execution or subprocess invocation.

The session does not implement native FFmpeg, HyperFrames, new output generation, captions, or advanced transitions. It creates the capability contract and selected-renderer plumbing those later sessions will use, with tests proving existing Editly behavior stays compatible.

---

## 2. Objectives

1. Add a typed renderer capability model and registry for Editly, `auto`, and future renderer identifiers.
2. Validate renderer-feature combinations with stable machine-readable unsupported-feature errors before compilation or worker execution.
3. Route API, sync render service, and async worker flows through explicit renderer selection while preserving Editly defaults.
4. Expose selected renderer context in existing render metadata, logs, and metrics without leaking raw composition payloads.

---

## 3. Prerequisites

### Required Sessions
- [x] `phase03-session01-postgresql-persistence-and-alembic-migrations` - Provides production persistence and migration discipline.
- [x] `phase03-session02-s3-compatible-storage-and-download-modes` - Provides durable artifact paths and centralized URL behavior.
- [x] `phase03-session03-api-key-authentication-and-access-control` - Provides API boundary protection for render submission.
- [x] `phase03-session04-limits-resource-controls-and-asset-security-hardening` - Provides request, asset, subprocess, and workspace guardrails.
- [x] `phase03-session05-operational-visibility-and-production-stack` - Provides renderer failure metrics and redacted operational visibility.

### Required Tools/Knowledge
- Pydantic v2 model validators and discriminated unions in `app/models/composition.py`.
- Renderer protocol, Editly compiler, and replay artifact behavior in `app/renderers/`.
- FastAPI dependency injection and render route behavior.
- Async worker status transitions and failure normalization.
- pytest, pytest-asyncio, and existing render service fixtures.

### Environment Requirements
- Python 3.11+ environment with project dependencies installed through `uv`.
- Existing SQLite-backed tests for composition schema, API render routes, worker pipeline, and metrics remain runnable.
- No new database tables are planned; any metadata changes must use the existing `renders.renderer` column or require an explicit Alembic migration.

---

## 4. Scope

### In Scope (MVP)
- Client can omit `renderer` or set `renderer` to `auto` and receive the same Editly-compatible behavior as before - resolve to Editly through a single selection helper.
- Client can request explicit `editly` rendering - validate against Editly's declared support before queueing or compiling.
- System can reject unsupported renderer names, assets, output formats, transitions, captions, and poster options with stable machine-readable errors - add a capability validation error model and map it to API/worker failure paths.
- System can declare future renderer names without implementing them - reserve capability records for `ffmpeg-native` and `hyperframes` only as unavailable or unsupported until their sessions implement them.
- Worker and sync service can persist and log the selected renderer - use existing `renders.renderer`, structured logs, and renderer failure metrics without raw payload logging.
- Tests prove default Editly selection, explicit Editly selection, invalid renderer rejection, unsupported feature rejection, async enqueue rejection, worker rejection, and metric/log renderer fields.
- Documentation explains renderer selection semantics and capability error responses for future adapter work.

### Out of Scope (Deferred)
- Native FFmpeg renderer implementation - Reason: scheduled for Session 05 after output formats and transition validation.
- HyperFrames renderer implementation - Reason: scheduled for Session 06 after the capability contract and FFmpeg subset exist.
- GIF, WebM, or PNG sequence rendering - Reason: Session 02 handles output generation and artifact behavior.
- Caption, subtitle, or poster customization implementation - Reason: Session 03 handles finishing controls.
- Advanced transition implementation - Reason: Session 04 handles schema expansion and Editly mapping.
- Browser or FFmpeg runtime sandboxing changes - Reason: Phase 03 guardrails remain the current production boundary.

---

## 5. Technical Approach

### Architecture

Add `app/renderers/capabilities.py` as the single source of renderer support declarations and validation helpers. It should define immutable capability data for supported asset types, output formats, transition types, optional feature flags, and renderer availability. The Editly record should reflect the current production implementation: video, image, text, audio, color assets; MP4 output; existing fade, fade_out, and crossfade transitions; no captions or custom poster controls yet.

Keep public schema parsing in `app/models/composition.py`, but move renderer compatibility rules out of generic Pydantic field parsing and into explicit capability validation. Pydantic can still restrict known renderer enum values in the current schema, but the capability validator should produce stable domain errors such as `UNSUPPORTED_RENDERER` and `UNSUPPORTED_RENDERER_FEATURE` with context identifying the renderer, feature path, and requested value.

Update renderer resolution so `auto` and omitted renderer select Editly for now, explicit `editly` selects Editly, and future names fail cleanly until their adapters are implemented. `RenderService` should depend on `RendererProtocol` or a resolver instead of being typed only to `EditlyRenderer`, while still receiving the default Editly renderer through existing FastAPI dependencies. Async submission should validate capability compatibility before queue admission and input persistence so invalid jobs do not enter Redis. Worker and sync paths should validate again before compile as a fail-closed defense for queued or replayed inputs.

Use the existing `renders.renderer` field for selected-renderer metadata; do not add a migration unless implementation discovers missing storage requirements. Logs should include renderer names and error codes, not full composition JSON, asset URLs, callback URLs, or compiled specs. Metrics already group renderer failures by `renders.renderer`, so the selected renderer must be written before or during compile failure handling.

### Design Patterns
- Single capability registry: Keep support declarations centralized so later renderer sessions extend one contract.
- Boundary validation: Reject unsupported combinations at API submission and again in the worker before compilation.
- Stable domain errors: Use typed exceptions and error codes rather than free-form `ValueError` text.
- Protocol-based renderer use: Keep services bound to the renderer protocol, not the Editly concrete class.
- Redacted observability: Log renderer selection and error codes without raw request payloads or secrets.

### Technology Stack
- Python 3.11+
- FastAPI 0.136.1 / Starlette 0.52.1
- Pydantic 2.11.2
- SQLModel / SQLAlchemy async sessions
- ARQ / Redis async worker path
- structlog
- pytest + pytest-asyncio

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/renderers/capabilities.py` | Typed renderer capability declarations, selection helpers, and validation errors | ~240 |
| `tests/test_renderer_capabilities.py` | Unit tests for default selection, explicit renderer names, capability checks, and stable error context | ~260 |
| `tests/test_renderer_selection_flow.py` | Integration-style tests for API, sync service, and worker validation paths | ~260 |
| `docs/renderer-capabilities.md` | Operator and developer documentation for renderer selection, support matrix, and error semantics | ~180 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/models/composition.py` | Align renderer/output/schema fields with capability validation boundaries and future feature placeholders where needed | ~70 |
| `app/models/error_codes.py` | Add stable unsupported renderer and unsupported feature error codes | ~20 |
| `app/models/errors.py` | Document unsupported renderer feature API responses | ~25 |
| `app/renderers/__init__.py` | Export capability helpers and adapt renderer resolution to the registry | ~60 |
| `app/renderers/base.py` | Ensure protocol signatures cover selected renderer metadata and current compile kwargs consistently | ~35 |
| `app/api/deps.py` | Provide renderer resolver or selected renderer dependencies without hard-coding Editly in service typing | ~45 |
| `app/api/routes_renders.py` | Validate renderer capabilities before queue admission and map errors to stable API responses | ~80 |
| `app/services/render_service.py` | Validate selected renderer before compile and store selected renderer consistently for sync and worker paths | ~100 |
| `app/workers/render_worker.py` | Revalidate queued compositions, persist renderer on failure paths, and log selected renderer safely | ~80 |
| `app/db/render_crud.py` | Add or adjust helper calls for selected-renderer persistence using the existing render column | ~35 |
| `tests/conftest.py` | Update renderer mocks and service fixtures for protocol/resolver behavior | ~45 |
| `tests/test_api_renders.py` | Cover invalid renderer and unsupported feature submission errors | ~120 |
| `tests/test_worker_pipeline.py` | Cover worker-side capability validation and failure metadata | ~100 |
| `tests/test_metrics.py` | Verify renderer failure metrics still group by selected renderer and redacted labels | ~40 |
| `README.md` | Link renderer capability behavior and default Editly selection | ~40 |
| `docs/ARCHITECTURE.md` | Document renderer protocol, capability registry, and future adapter flow | ~90 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Requests without `renderer` continue to use Editly-compatible behavior.
- [ ] Requests with `renderer: "auto"` resolve to Editly while the registry has no more specific supported renderer.
- [ ] Requests with explicit `renderer: "editly"` validate and use Editly.
- [ ] Requests with unavailable future renderer names fail before job execution with a stable machine-readable error.
- [ ] Unsupported renderer-feature combinations fail before renderer invocation with renderer, feature path, and requested value in bounded error context.
- [ ] Async render submissions reject invalid renderer combinations before Redis enqueue.
- [ ] Worker and sync paths revalidate renderer compatibility before compile for fail-closed replay and queued-job behavior.
- [ ] Selected renderer is written to render metadata and appears in logs/metrics without raw payload leakage.

### Testing Requirements
- [ ] Unit tests written and passing for registry lookup, auto/default selection, explicit selection, and unsupported features.
- [ ] API tests written and passing for valid defaults, explicit Editly, invalid renderer, and unsupported output/feature combinations.
- [ ] Worker tests written and passing for queued invalid compositions and failure metadata.
- [ ] Metrics/logging tests written and passing for selected renderer labels and redaction.
- [ ] Manual testing completed for one valid default render submission and one invalid renderer submission.

### Non-Functional Requirements
- [ ] Validation is deterministic and does not inspect or fetch remote assets.
- [ ] Error responses avoid raw composition bodies, asset URLs, callback URLs, filesystem paths, and secrets.
- [ ] Capability registry additions require no route-handler changes for future renderer sessions.
- [ ] Existing Editly compiler tests and render API tests remain compatible.

### Quality Gates
- [ ] All files ASCII-encoded.
- [ ] Unix LF line endings.
- [ ] Code follows project conventions.

---

## 8. Implementation Notes

### Key Considerations
- `Composition.renderer` already exists and accepts `auto`, `editly`, `ffmpeg-native`, and `hyperframes`. This session should decide whether unknown names remain Pydantic errors or become capability errors; either way, API output must be stable and documented.
- `OutputFormat` already includes MP4, GIF, WebM, and PNG sequence values, but current Editly compilation always writes MP4. Capability validation should reject non-MP4 formats for Editly until Session 02 implements output generation.
- `RenderService` is currently typed to `EditlyRenderer` and stores `self._renderer.name`. Updating that boundary to `RendererProtocol` or a resolver is the central code change.
- Async `POST /v1/renders` currently validates limits before queue admission. Renderer capability validation should run near that limit check so unsupported jobs do not consume storage writes or queue slots.
- Worker validation remains necessary because queued input can predate code changes, be replayed from storage, or bypass API tests.
- The existing `renders.renderer` column can store selected renderer names. Do not introduce a migration unless implementation discovers a missing durable field.

### Potential Challenges
- Pydantic request validation returns FastAPI's default 422 shape, while capability errors should use VidAPI's stable error envelope. Keep expectations explicit in tests.
- Future renderer names are currently accepted by the `RendererChoice` literal, but no adapters exist. The registry should distinguish "known but unavailable" from "unknown" if both are representable.
- Capability validation must walk nested tracks and clips without mutating the frozen composition models.
- Existing tests use `MagicMock(spec=EditlyRenderer)`. Protocol-based typing and resolver injection may require fixture adjustments.
- If compile failures happen before renderer metadata is persisted, metrics may group failures under `unknown`. Store selected renderer before risky compile work when possible.

### Relevant Considerations
- [P03] **Centralized artifact URL resolution**: Keep renderer metadata and future artifact behavior centralized rather than adding duplicate URL logic in routes.
- [P03] **Redaction discipline**: Renderer validation logs and errors must avoid raw payloads, asset URLs, callback URLs, presigned URLs, and secrets.
- [P03] **Guardrail tuning is deployment-specific**: Capability validation complements resource limits but should not replace existing duration, fps, resolution, asset, and queue guardrails.
- [P03] **Fail-closed production startup**: If this session touches durable metadata, migrations and metadata must stay aligned.
- [P02] **Pure-function segment compiler**: Keep registry and validation helpers pure and easy to unit test.
- [P02] **Replay metadata (`replay.json`)**: Selected renderer should remain clear in replay metadata for later adapter parity work.

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Invalid renderer combinations enter the queue and fail later with ambiguous compile errors.
- Capability errors expose raw composition content, asset URLs, callback URLs, or storage paths.
- Default renderer behavior changes for existing clients that omit `renderer`.
- Failure metrics continue grouping selected renderer failures as `unknown`.

---

## 9. Testing Strategy

### Unit Tests
- Test registry lookup for Editly, `auto`, unavailable future renderers, and unknown names.
- Test capability validation for supported Editly MP4 compositions with video, image, text, audio, and color assets.
- Test rejection for GIF, WebM, PNG sequence, unavailable renderer names, unsupported feature placeholders, and unsupported transitions where applicable.
- Test error objects include stable code, renderer, feature path, requested value, and bounded safe context.

### Integration Tests
- Test `POST /v1/renders` accepts omitted renderer, `auto`, and explicit `editly`.
- Test `POST /v1/renders` rejects unsupported output formats before queue admission in async mode.
- Test sync render path stores selected renderer and preserves existing output behavior.
- Test worker path fails queued invalid compositions before compile and persists renderer/error metadata.

### Manual Testing
- Submit a minimal MP4 composition without `renderer` and confirm the response remains accepted.
- Submit the same composition with `renderer: "editly"` and confirm selected renderer metadata is `editly`.
- Submit a composition with `renderer: "ffmpeg-native"` before that adapter exists and confirm a stable unsupported renderer error.
- Submit a composition with `output.format: "webm"` and `renderer: "editly"` and confirm a stable unsupported feature error.

### Edge Cases
- `renderer` omitted, null, and `auto` all select the same default.
- Future renderer names are known but unavailable until their implementation sessions.
- Empty or malformed timelines still fail through existing Pydantic validation before capability validation.
- Multiple unsupported features return deterministic, bounded error details.
- Validation errors never include full asset URLs, callback URLs, raw input JSON, or compiled specs.

---

## 10. Dependencies

### External Libraries
- No new external libraries planned.

### Other Sessions
- **Depends on**: Phase 03 completed.
- **Depended by**: `phase04-session02-output-formats-and-presets`, `phase04-session03-captions-and-poster-customization`, `phase04-session04-advanced-transitions-and-feature-validation`, `phase04-session05-native-ffmpeg-renderer-subset`, `phase04-session06-hyperframes-renderer-adapter`.

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
