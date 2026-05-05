# Session Specification

**Session ID**: `phase02-session04-transitions-and-positioning`
**Phase**: 02 - Templates and Polish
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session wires the existing Position, Offset, and Transition Pydantic models into the Editly rendering pipeline so that clips are placed at named positions with optional offsets and rendered with fade/crossfade transitions. The schema models already exist on the Clip type but the segment compiler and layer mappers currently ignore them entirely -- no position, offset, opacity, scale, or transition data reaches the compiled Editly JSON.

The work breaks into three pillars: (1) position resolution -- converting NamedPosition enums and CoordinatePosition values plus optional Offset into Editly-compatible layer positioning properties; (2) transition emission -- adding fadeIn, fadeOut, and crossfade directives to the Editly clip spec; and (3) validation tightening -- restricting the free-form Transition.name string to a supported enum and producing clear errors for unsupported combinations. Tests will cover each pillar independently and verify backward compatibility for existing compositions that omit these optional fields.

This session directly addresses the Phase 02 PRD deliverable "named positions and offsets, basic fades, and crossfade transitions where supported by the selected renderer" and enables more expressive video compositions before Phase 02 closes out.

---

## 2. Objectives

1. Propagate clip position, offset, opacity, and scale into Editly layer output so clips render at their specified location
2. Emit fadeIn, fadeOut, and crossfade transition directives in the compiled Editly spec
3. Restrict Transition.name to a validated enum of supported transition types with clear error messages for unsupported values
4. Maintain full backward compatibility -- compositions without position/offset/transition fields must render identically to before

---

## 3. Prerequisites

### Required Sessions
- [x] `phase02-session03-webhook-delivery-system` - Webhook system complete; no schema dependencies but sequencing required
- [x] `phase01-session04-multi-track-and-audio-mixing` - Segment compiler with z-order and audio mixing operational
- [x] `phase00-session04-editly-renderer-and-segment-compiler` - Core segment compiler and Editly renderer

### Required Tools/Knowledge
- Editly layer positioning model (position property on layers, overlay coordinates)
- Editly clip-level transition support (transition property with name and duration)
- FFmpeg overlay filter coordinate system for position validation

### Environment Requirements
- Python 3.11+ with project dependencies installed
- Node.js + Editly available for integration testing
- Test fixtures from tests/fixtures/

---

## 4. Scope

### In Scope (MVP)
- Position resolution: NamedPosition enum to Editly-compatible layer position - map all 9 named positions
- Position resolution: CoordinatePosition (normalized 0-1) to Editly layer coordinates
- Offset application: Adjust resolved position by x/y pixel offset
- Opacity propagation: Pass clip opacity to Editly layer output
- Scale propagation: Pass clip scale to Editly layer output where supported
- Transition enum: Replace free-form string with validated TransitionType enum (fadeIn, fadeOut, crossfade)
- Transition emission: Add Editly clip-level transition for fadeIn/fadeOut
- Crossfade emission: Detect sequential clips on the same track and emit crossfade
- Validation: Reject unsupported transition names with clear 422 errors
- Backward compatibility: All existing compositions without these fields render identically

### Out of Scope (Deferred)
- Complex transitions (wipe, slide, zoom, dissolve) - *Reason: Not supported by Editly MVP*
- Keyframed transforms or animation - *Reason: Phase 04 advanced rendering*
- Per-renderer transition capability discovery API - *Reason: Only one renderer exists*
- Position/transition support for non-Editly renderers - *Reason: Only Editly implemented*

---

## 5. Technical Approach

### Architecture
Position resolution lives as a pure function module that maps (NamedPosition|CoordinatePosition, Offset|None, output_width, output_height) to (x, y) pixel coordinates. Layer mappers in editly.py call the resolver and inject position/opacity/scale into layer dicts. The Editly spec assembler handles transitions at the clip level by setting the `transition` property on Editly clips.

### Design Patterns
- Pure functions for position resolution: Stateless, testable, composable (consistent with segment compiler pattern from CONSIDERATIONS.md)
- Enum validation: Replace free-form string Transition.name with a Literal/StrEnum for compile-time safety
- Adapter pattern: Position resolver adapts VidAPI's coordinate model to Editly's layer positioning model

### Technology Stack
- Python 3.11+ with Pydantic v2
- Editly (Node subprocess) for rendering verification
- pytest + pytest-asyncio for testing

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/renderers/position.py` | Position resolution: named/coordinate to Editly coords | ~80 |
| `tests/test_position_resolver.py` | Unit tests for position resolution logic | ~150 |
| `tests/test_transitions.py` | Unit tests for transition validation and emission | ~120 |

### Files to Modify
| File | Changes | Est. Lines Changed |
|------|---------|------------|
| `app/models/composition.py` | Replace Transition.name string with TransitionType enum | ~15 |
| `app/renderers/editly.py` | Update layer mappers and spec assembler for position/transition | ~80 |
| `tests/test_editly_compiler.py` | Add tests for positioned layers and transitions in compiled specs | ~60 |
| `tests/test_segment_compiler.py` | Add tests for transition-aware segment handling | ~30 |
| `tests/test_composition_schema.py` | Update transition validation tests for enum | ~20 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Named positions correctly map to Editly layer positioning for all 9 enum values
- [ ] CoordinatePosition (0-1 normalized) maps to pixel coordinates relative to output dimensions
- [ ] Offsets adjust the resolved position by x/y values
- [ ] Opacity propagates to Editly layer output
- [ ] fadeIn transition emits correct Editly clip transition
- [ ] fadeOut transition emits correct Editly clip transition
- [ ] crossfade transition emits correct Editly clip-level crossfade between sequential clips
- [ ] Unsupported transition names produce 422 validation errors
- [ ] Existing compositions without position/offset/transition render identically

### Testing Requirements
- [ ] Unit tests for position resolver covering all 9 named positions
- [ ] Unit tests for coordinate position with and without offset
- [ ] Unit tests for transition emission in Editly spec
- [ ] Unit tests for crossfade detection between sequential clips
- [ ] Unit tests for unsupported transition rejection
- [ ] Backward compatibility test with existing fixture compositions

### Non-Functional Requirements
- [ ] No regression in existing test suite (457+ tests passing)
- [ ] All new code has type annotations

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (CONVENTIONS.md)

---

## 8. Implementation Notes

### Key Considerations
- Editly uses a `position` property on layers that accepts either a named string or an object with `x`, `y`, `originX`, `originY`
- Editly supports `transition` at the clip level with `name` and `duration` fields
- The segment compiler splits overlapping clips into non-overlapping segments; crossfade must be handled at the segment boundary level
- Opacity in Editly is typically handled via `mixVolume` for video/audio and layer-level opacity for overlays

### Potential Challenges
- Crossfade between segments: Editly crossfade requires adjacent clips to share a transition boundary. The segment compiler creates discrete segments, so crossfade must be emitted on the Editly clip that follows the transition point.
- Position coordinate systems: Editly may use different coordinate origins depending on layer type. The resolver must account for this.
- Scale interaction with position: Scaled layers change effective size, which may affect position anchor points.

### Relevant Considerations
- [P00] **Pure-function segment compiler**: Position resolution follows the same stateless pure-function pattern for testability
- [P00] **Single renderer implemented**: All transition/position support targets Editly only; reject unsupported combinations
- [P00] **Discriminated unions for asset types**: Extend the same pattern with TransitionType enum for type safety

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Transition on clip that is the only clip in a track (crossfade requires a neighbor -- handle gracefully)
- Position resolution with extreme offset values pushing content off-screen (validate or clamp)
- Backward compatibility regression when existing clips have default position=center and no transition

---

## 9. Testing Strategy

### Unit Tests
- Position resolver: all 9 named positions at multiple output dimensions
- Position resolver: coordinate positions with and without offsets
- Layer mapper: verify position/opacity/scale propagate to Editly layer dict
- Transition emission: fadeIn, fadeOut on single clips
- Crossfade: sequential clips on same track, clips on different tracks (no crossfade)

### Integration Tests
- Full compile() with positioned clips produces valid Editly JSON
- Full compile() with transitions produces valid Editly JSON
- Backward compatibility: compile existing fixtures without position/transition

### Manual Testing
- Render a composition with clips at each named position
- Render a composition with fadeIn/fadeOut transitions
- Render a composition with crossfade between two sequential video clips

### Edge Cases
- Crossfade on single-clip track (should be ignored or produce fadeIn only)
- Transition duration longer than clip length (should be clamped or rejected)
- Offset that moves clip partially off-screen (should apply without error)
- CoordinatePosition at boundary values (0.0, 1.0)
- Multiple transitions on overlapping clips across tracks

---

## 10. Dependencies

### External Libraries
- No new external libraries required

### Other Sessions
- **Depends on**: `phase02-session03-webhook-delivery-system`, `phase01-session04-multi-track-and-audio-mixing`
- **Depended by**: `phase02-session05-audio-polish-and-hardening`

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
