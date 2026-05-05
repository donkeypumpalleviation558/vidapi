# Session Specification

**Session ID**: `phase04-session04-advanced-transitions-and-feature-validation`
**Phase**: 04 - Advanced Rendering
**Status**: Complete
**Created**: 2026-05-05

---

## 1. Session Overview

This session expands VidAPI transition support beyond the current fade-only public behavior while keeping transition handling behind the renderer-independent composition schema. The existing implementation supports `fade_in`, `fade_out`, and `crossfade`, then maps all emitted Editly transitions to `fade`. Session 04 adds a bounded allowlist of Editly-backed visual transition effects and makes transition validation explicit before expensive render work starts.

The work is intentionally focused on transition schema, semantic validation, capability validation, deterministic compiler output, and documentation. It does not introduce native FFmpeg rendering, HyperFrames support, custom shaders, arbitrary GL transition parameters, or keyframed transforms. Those stay deferred so this session remains a stable 2-4 hour implementation pass.

The main reliability improvement is that invalid transition timing and track interactions should fail at admission or worker revalidation instead of compiling to a no-op or silently choosing one transition from several conflicting candidates. Editly only supports one clip-level transition at an output segment boundary, so VidAPI must define that constraint clearly and test it.

---

## 2. Objectives

1. Add a renderer-independent public transition allowlist for supported advanced effects with deterministic aliases and placement rules.
2. Validate transition timing, clip boundary, overlap, and same-boundary conflict cases before renderer invocation.
3. Map supported VidAPI transition values to Editly transition names without exposing Editly-native schemas or arbitrary params.
4. Update renderer capability checks, compiler tests, and documentation so unsupported renderer-transition combinations produce clear errors.

---

## 3. Prerequisites

### Required Sessions
- [x] `phase04-session01-renderer-capability-registry` - Provides renderer selection and unsupported-feature validation.
- [x] `phase04-session02-output-formats-and-presets` - Provides output format capability validation and shared render finishing behavior.
- [x] `phase04-session03-captions-and-poster-customization` - Confirms capability validation still runs at API admission and worker revalidation.
- [x] `phase02-session04-transitions-and-positioning` - Provides the current transition enum, placement validation, and Editly boundary emission.
- [x] `phase03-session04-limits-resource-controls-and-asset-security-hardening` - Provides shared composition limit validation for API and worker paths.

### Required Tools/Knowledge
- Pydantic v2 enum parsing and frozen value objects in `app/models/composition.py`.
- Current renderer capability registry and bounded error context in `app/renderers/capabilities.py`.
- Editly segment compiler functions in `app/renderers/editly.py`.
- Existing transition tests in `tests/test_transitions.py` and compiler tests in `tests/test_editly_compiler.py`.
- Editly transition reference in `references/editly/src/transition.ts` and `references/editly/examples/transitions.json5`.

### Environment Requirements
- Python 3.11+ dependencies installed with `uv`.
- Existing targeted tests runnable with pytest.
- FFmpeg and Node/Editly available only for optional manual render verification; unit tests should not require real long renders.
- No database schema or seed fixture change is expected for this session.

---

## 4. Scope

### In Scope (MVP)
- Client can request a bounded set of advanced inter-clip transitions - add explicit VidAPI values such as directional, wipe, zoom, circle, and blur effects with stable aliases and placement `between`.
- System can validate transition duration against outgoing and incoming clip lengths - reject overlong transitions before renderer invocation.
- System can validate transition boundary requirements - reject between transitions without an exact same-track successor, overlapping same-track clips, or gaps where a between transition cannot apply.
- System can validate track interactions - reject multiple incompatible transition requests at the same rendered boundary rather than silently dropping lower-priority transitions.
- System can keep `fade_in`, `fade_out`, and `crossfade` backward compatible - existing requests and compiled specs remain valid.
- Editly compiler can map supported public values to deterministic Editly transition names - no arbitrary Editly transition strings, params, random transitions, or custom shader inputs.
- Renderer capability checks can reject unsupported transition values for future renderers with bounded, redacted context.
- Tests cover schema aliases, semantic timing failures, capability failures, deterministic compiler output, and API admission behavior.
- Documentation explains supported transitions, placement rules, timing constraints, fallback semantics, and renderer capability behavior.

### Out of Scope (Deferred)
- Custom shader or arbitrary FFmpeg filter injection - Reason: unsafe and explicitly excluded by the session stub.
- Arbitrary gl-transition names or parameter objects - Reason: this would expose renderer internals and weaken capability validation.
- Keyframed transforms outside transition scope - Reason: explicitly deferred by the session stub.
- HyperFrames transition implementation - Reason: scheduled after the HyperFrames adapter exists.
- Native FFmpeg transition implementation - Reason: Session 05 owns the native FFmpeg renderer subset.
- A transition discovery endpoint - Reason: documentation and capability errors are enough for this phase.

---

## 5. Technical Approach

### Architecture

Keep the public schema renderer-independent by adding explicit enum values in `TransitionType` rather than accepting free-form renderer transition names. The initial advanced subset should map to Editly-supported transitions already present in the local reference: directional aliases, wipe directions, `crosszoom`, `simplezoom`, `circleopen`, and `linearblur`. Public names should use VidAPI's snake-case style while the compiler owns the mapping to Editly names.

Create a small transition helper module under `app/renderers/` that contains the public-to-Editly mapping and pure validation helpers. The helper should inspect tracks and clips, build boundary facts, and reject invalid between-transition cases with stable field paths. Shared composition limit validation should call this helper so direct render requests, template renders, and worker revalidation all receive the same failure behavior.

Update the Editly assembler to call the shared mapping helper instead of hard-coding `fade` in `_map_transition_to_editly`. Preserve current fade and crossfade behavior, but make advanced transitions compile deterministically at the selected boundary. Because Editly accepts one transition per output clip boundary, conflicting transition requests at one boundary should be rejected before compile rather than resolved implicitly.

### Design Patterns
- Enum allowlist: keep the public contract explicit and renderer-independent.
- Pure validation helper: compute transition boundary facts without mutating composition models.
- Boundary validation: fail before queue admission when timing, overlap, or track interaction rules cannot be honored.
- Capability boundary: reject unsupported renderer-transition combinations closest to request admission and again in the worker.
- Deterministic compiler mapping: produce stable Editly JSON with sorted/explicit mapping and no random transitions.

### Technology Stack
- Python 3.11+
- FastAPI 0.136.1 / Starlette 0.52.1
- Pydantic 2.11.2
- Editly renderer bridge
- pytest + pytest-asyncio, ruff, mypy

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/renderers/transitions.py` | Public transition mapping, boundary validation, and Editly transition planning helpers | ~220 |
| `docs/transitions.md` | Public transition documentation with examples, timing rules, and renderer support notes | ~160 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/models/composition.py` | Add advanced transition enum values, aliases, and placement rules | ~80 |
| `app/renderers/capabilities.py` | Expand Editly transition capability set and preserve bounded unsupported-feature context | ~60 |
| `app/renderers/editly.py` | Use shared transition mapping and validation output when assembling Editly specs | ~90 |
| `app/services/limits.py` | Call transition semantic validation in shared composition limit checks | ~70 |
| `docs/ARCHITECTURE.md` | Document transition validation and compiler flow | ~40 |
| `docs/renderer-capabilities.md` | Update transition support matrix and error semantics | ~50 |
| `README.md` | Add compact transition example and link to transition docs | ~40 |
| `tests/test_transitions.py` | Cover aliases, placement, timing, overlap, boundary, and conflict validation | ~220 |
| `tests/test_renderer_capabilities.py` | Cover advanced transition support and unsupported renderer context | ~90 |
| `tests/test_editly_compiler.py` | Cover deterministic Editly mapping for advanced transitions and backward compatibility | ~120 |
| `tests/test_api_renders.py` | Cover admission errors for invalid transition timing and clear success for supported transitions | ~100 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Existing `fade_in`, `fade_out`, and `crossfade` requests remain schema-valid and compile as before.
- [ ] Supported advanced transition values compile to deterministic Editly transition names.
- [ ] Aliases for public transition names normalize to one VidAPI enum value.
- [ ] Between transitions without an exact same-track successor fail before renderer invocation.
- [ ] Between transitions across gaps, same-track overlaps, or overlong durations fail with clear field context.
- [ ] Multiple incompatible transition requests at one rendered boundary fail instead of silently dropping one.
- [ ] Unsupported renderer-transition combinations return `UNSUPPORTED_RENDERER_FEATURE` with bounded context.
- [ ] Existing output format, caption, poster, and renderer selection behavior remains unchanged.

### Testing Requirements
- [ ] Unit tests written and passing for schema aliases, placement defaults, and invalid placement.
- [ ] Unit tests written and passing for transition semantic validation across gaps, overlaps, duration bounds, and track conflicts.
- [ ] Compiler tests written and passing for deterministic Editly transition mapping and default fixture compatibility.
- [ ] API tests written and passing for valid advanced transitions and invalid timing errors.
- [ ] Manual testing completed for one advanced transition render and one invalid transition request where local renderer dependencies are available.

### Non-Functional Requirements
- [ ] Transition validation uses no network, filesystem, subprocess, or renderer side effects.
- [ ] Capability and limit error context does not include asset URLs, callback URLs, storage paths, renderer specs, stack traces, or secrets.
- [ ] Public transition values remain renderer-independent and do not expose arbitrary Editly names or params.
- [ ] Compiler output remains deterministic for identical input JSON and assets.

### Quality Gates
- [ ] All files ASCII-encoded.
- [ ] Unix LF line endings.
- [ ] Code follows project conventions.

---

## 8. Implementation Notes

### Key Considerations
- Current `TransitionType` has only `fade_in`, `fade_out`, and `crossfade`; the advanced subset should be additive.
- Current `_map_transition_to_editly()` always emits `{"name": "fade"}`. This needs to become a public-to-renderer mapping without accepting free-form renderer strings.
- Current `_find_transition_at_boundary()` silently picks one candidate by priority and track index. This session should make conflicting boundary requests invalid before compilation.
- `validate_composition_limits()` already runs in direct render, template render, and worker paths, making it the right place to wire pure semantic transition validation.
- No Alembic migration is needed because transitions are part of the stored composition JSON, not new relational metadata.

### Potential Challenges
- Editly names are case-insensitive internally, but VidAPI should emit one canonical spelling for deterministic JSON.
- Some existing fade-in behavior depends on a preceding gap; new validation should preserve existing accepted cases while making no-op between transitions fail clearly.
- Multi-track timelines can request several transitions at the same boundary even though Editly has one clip-level transition slot. Rejecting conflicts is safer than implicit top-track selection.
- Template renders expand variables before validation, so transition validation must work on the expanded composition and not assume raw template input.

### Relevant Considerations
- [P03] **Guardrail tuning is deployment-specific**: Transition validation should bound timing and track interactions before expensive render work.
- [P03] **Redaction discipline**: Error context must include enum-like transition values and field paths only, never composition payloads or asset URLs.
- [P02] **Pure-function segment compiler**: Keep transition planning stateless and deterministic for focused tests.
- [P02] **Replay metadata (`replay.json`)**: Advanced transitions should appear only through the deterministic compiled renderer spec and replay artifacts already produced by the renderer.

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Invalid transitions pass API validation and become no-op or ambiguous renderer behavior.
- Multiple transitions at one Editly boundary produce nondeterministic or silently dropped output.
- Free-form transition names expose renderer internals and bypass capability validation.
- Capability errors leak raw composition, asset, or callback data.
- Existing fade/crossfade fixtures regress while adding the advanced subset.

---

## 9. Testing Strategy

### Unit Tests
- Validate transition enum parsing, aliases, placement rules, and duration bounds.
- Validate boundary helper behavior for same-track successors, gaps, overlaps, end-of-track cases, and same-boundary conflicts.
- Validate renderer capability acceptance and rejection for transition values.

### Integration Tests
- Compile supported advanced transitions and assert deterministic Editly JSON.
- Submit valid and invalid render requests through the API and verify success or structured 422 responses.
- Verify template-backed renders receive the same validation after expansion where practical.

### Manual Testing
- Render a short two-clip composition with one directional or wipe transition.
- Submit a cross-track or gap-based invalid transition and confirm the API returns a bounded validation error before queueing.

### Edge Cases
- Advanced transition on final clip with no successor.
- Advanced transition between same-track clips with a tiny epsilon mismatch.
- Advanced transition duration longer than the outgoing or incoming clip.
- Two tracks requesting different transitions at the same output boundary.
- Existing compositions with no transition field.

---

## 10. Dependencies

### External Libraries
- None added.

### Other Sessions
- **Depends on**: `phase04-session01-renderer-capability-registry`, `phase04-session02-output-formats-and-presets`, `phase04-session03-captions-and-poster-customization`, `phase02-session04-transitions-and-positioning`
- **Depended by**: `phase04-session05-native-ffmpeg-renderer-subset`, `phase04-session06-hyperframes-renderer-adapter`

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
