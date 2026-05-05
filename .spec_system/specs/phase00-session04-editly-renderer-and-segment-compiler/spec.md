# Session Specification

**Session ID**: `phase00-session04-editly-renderer-and-segment-compiler`
**Phase**: 00 - Foundation
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session implements the renderer abstraction layer and the Editly renderer bridge -- the core engine that transforms VidAPI's absolute-time JSON compositions into rendered MP4 video files. The renderer protocol provides a stable interface that future renderers (FFmpeg-native, HyperFrames) will also implement, keeping the rest of the codebase renderer-agnostic.

The centerpiece is the segment compiler, which converts VidAPI's absolute-time timeline model (where each clip has a `start` and `length` in seconds) into Editly's sequential clip model. This involves collecting all clip boundaries, sorting them, generating non-overlapping time segments, and mapping active clips into Editly layers for each segment. This is the highest-risk component in Phase 00 because incorrect segment slicing produces wrong video output that is hard to debug.

The session also delivers poster generation (extracting a thumbnail frame from rendered output via FFmpeg), replay metadata for debugging failed renders, and a focused test suite for the segment compiler covering all core timeline scenarios.

---

## 2. Objectives

1. Define the renderer protocol (`compile` + `render`) so all future renderers share one interface
2. Implement the Editly renderer bridge: segment compiler, layer mapper, subprocess invocation, and artifact collection
3. Achieve deterministic compiled Editly JSON output for reproducible builds and golden-file tests
4. Generate poster thumbnails from rendered output via FFmpeg subprocess
5. Build a comprehensive segment compiler test suite covering single-clip, sequential, overlapping, gap, and z-order scenarios

---

## 3. Prerequisites

### Required Sessions
- [x] `phase00-session01-project-skeleton-and-config` - FastAPI skeleton, config, DB session
- [x] `phase00-session02-composition-schema-and-db-models` - Pydantic composition models, DB render model
- [x] `phase00-session03-storage-and-asset-service` - Storage protocol, local storage, asset service, text renderer, ffprobe

### Required Tools/Knowledge
- Editly npm package (installed globally or via npx in worker environment)
- FFmpeg 6+ with ffprobe on PATH
- Node.js runtime for Editly subprocess

### Environment Requirements
- Python 3.11+ with project dependencies installed
- Write access to `data/renders/` workspace directory

---

## 4. Scope

### In Scope (MVP)
- Renderer protocol with `compile()` and `render()` methods - abstract base for all renderers
- Compiled render result dataclass capturing the renderer spec, replay metadata, and workspace paths
- Render artifact dataclass capturing output path, poster path, log path, and timing
- Segment compiler algorithm: collect boundaries, sort, deduplicate, generate non-overlapping segments with active clip layers
- VidAPI-to-Editly layer mapping for video, image, text (pre-rendered PNG), audio, and color assets
- Fit mode translation (cover/contain/stretch to Editly resizeMode)
- Soundtrack mapping to Editly audioTracks/audioFilePath
- Editly subprocess invocation via `asyncio.create_subprocess_exec` with timeout and resource limits
- Full stderr capture and structured log persistence
- Replay metadata generation (command, args, environment, input/output paths)
- Poster generation via FFmpeg frame extraction from rendered output
- Deterministic JSON serialization for compiled Editly specs
- Segment compiler unit tests for all core scenarios
- Editly compiler integration test (compile only, no subprocess)

### Out of Scope (Deferred)
- Multi-track advanced compositing improvements - *Reason: Phase 01*
- Complex transitions beyond basic fade - *Reason: Phase 02*
- Native FFmpeg renderer implementation - *Reason: Phase 04*
- HyperFrames renderer implementation - *Reason: Phase 04*
- Actual render execution integration tests requiring Editly installed - *Reason: optional, environment-dependent*

---

## 5. Technical Approach

### Architecture
The renderer lives behind a protocol interface. The Editly renderer implements `compile()` to transform VidAPI's `Composition` into an Editly JSON spec, and `render()` to invoke the Editly Node subprocess and collect artifacts. The segment compiler is the heart of `compile()` -- it slices absolute-time clips into non-overlapping sequential segments that Editly can process.

```
Composition (VidAPI JSON)
    |
    v
EditlyRenderer.compile()
    |-- Segment compiler: absolute-time -> sequential segments
    |-- Layer mapper: VidAPI assets -> Editly layers
    |-- Audio mapper: soundtrack -> audioTracks
    v
CompiledRender (compiled.editly.json + replay.json)
    |
    v
EditlyRenderer.render()
    |-- Subprocess: node editly --json compiled.editly.json
    |-- Stderr capture -> logs.txt
    |-- Timeout + exit code handling
    v
RenderArtifact (output.mp4 + poster.jpg + logs)
```

### Design Patterns
- **Protocol pattern**: Renderer protocol enables pluggable backends without inheritance coupling
- **Dataclass results**: `CompiledRender` and `RenderArtifact` are frozen dataclasses for immutable result passing
- **Boundary sorting algorithm**: Segment compiler uses a sweep-line approach over sorted time boundaries
- **Deterministic serialization**: `json.dumps` with `sort_keys=True` and consistent formatting

### Technology Stack
- Python 3.11+ with asyncio subprocess management
- Editly (Node.js) invoked as subprocess
- FFmpeg for poster generation
- Pydantic v2 models from Session 02
- structlog for structured logging
- pytest + pytest-asyncio for testing

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/renderers/base.py` | Renderer protocol, CompiledRender, RenderArtifact dataclasses | ~80 |
| `app/renderers/editly.py` | Editly renderer: segment compiler, layer mapper, subprocess runner | ~450 |
| `app/renderers/poster.py` | Poster generation via FFmpeg frame extraction | ~80 |
| `tests/test_segment_compiler.py` | Segment compiler unit tests (8-10 scenarios) | ~350 |
| `tests/test_editly_compiler.py` | Editly compile integration tests (no subprocess) | ~200 |
| `tests/test_poster.py` | Poster generation tests | ~60 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/renderers/__init__.py` | Export renderer protocol and Editly renderer | ~10 |
| `app/core/config.py` | Add Editly and poster configuration settings | ~15 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Segment compiler correctly splits overlapping clips into non-overlapping segments
- [ ] Single clip, sequential clips, overlapping clips, and gap cases produce correct Editly JSON
- [ ] Track z-order is preserved in segment layer ordering
- [ ] Video and image assets map to correct Editly layer types with path and resizeMode
- [ ] Text assets use pre-rendered Pillow PNGs as image-overlay layers
- [ ] Color assets map to fill-color or background layers
- [ ] Soundtrack maps to Editly audioTracks
- [ ] Compiled Editly JSON is deterministic for the same input
- [ ] Editly subprocess runs with explicit timeout and captures full stderr
- [ ] Non-zero exit code, timeout, and missing output file are treated as render failures
- [ ] Poster is generated from rendered output via FFmpeg frame extraction
- [ ] replay.json captures command, args, environment, and paths for manual re-run

### Testing Requirements
- [ ] Segment compiler tests cover: single clip, two sequential clips, overlapping clips on different tracks, gaps, text overlay partial coverage, asset trim offsets, track z-order, soundtrack inclusion
- [ ] Editly compile tests verify output JSON structure for representative compositions
- [ ] Poster generation test verifies FFmpeg invocation logic
- [ ] All tests pass with `pytest`

### Non-Functional Requirements
- [ ] Compiled JSON output is reproducible (same input -> byte-identical JSON)
- [ ] Subprocess timeout prevents runaway renders

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (CONVENTIONS.md)
- [ ] No direct Editly/FFmpeg calls outside renderer abstraction

---

## 8. Implementation Notes

### Key Considerations
- The segment compiler is the most important MVP implementation risk; thorough tests are critical
- Editly uses sequential clips with `duration`, while VidAPI uses absolute `start` + `length`; the compiler must bridge these models precisely
- Text assets are already rendered to PNG by the asset service (Session 03); the Editly renderer treats them as image overlays
- Audio handling: Editly supports `audioTracks` at the top level and clip-level audio; start with `audioTracks` for soundtrack

### Potential Challenges
- **Floating-point boundary arithmetic**: Use rounding to avoid micro-gaps between segments; mitigate with epsilon tolerance
- **Editly layer type mapping**: Not all VidAPI features have direct Editly equivalents; document unsupported cases and reject or degrade gracefully
- **Subprocess environment**: Editly needs Node.js on PATH; tests that invoke the actual subprocess may fail in environments without Node/Editly installed
- **Poster extraction timing**: Need to pick an appropriate frame (e.g., 25% into the video or first frame) for the poster thumbnail

### Relevant Considerations
- **FFmpeg subprocess spawning needs resource limits**: Apply explicit timeout and memory considerations to both Editly and FFmpeg poster subprocesses
- **Text rendering via Pillow has limited typography**: Accept this limitation for MVP; text is pre-rendered to PNG by Session 03's text renderer
- **Avoid MoviePy wrapper**: Build directly on Editly subprocess and FFmpeg CLI, not abstraction layers

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session's deliverables:
- Subprocess invocation without timeout leads to hung renders (mitigate: explicit asyncio timeout + kill on expiry)
- Floating-point segment boundaries create micro-gaps or overlaps in compiled output (mitigate: epsilon rounding in boundary deduplication)
- Non-zero exit code swallowed silently leaves render in wrong state (mitigate: explicit exit code check + stderr capture + error mapping)

---

## 9. Testing Strategy

### Unit Tests
- Segment compiler boundary collection and deduplication
- Segment generation from boundaries
- Active clip resolution per segment
- Layer mapping for each asset type (video, image, text PNG, color)
- Fit mode translation
- Audio/soundtrack mapping
- Deterministic JSON output comparison

### Integration Tests
- Full compile pipeline: Composition -> compiled Editly JSON (no subprocess)
- Verify compiled JSON structure matches Editly expectations
- Poster generation command construction

### Manual Testing
- Inspect compiled.editly.json for a sample composition with image + text overlay + soundtrack
- Verify replay.json contains runnable command info

### Edge Cases
- Zero-length clip rejection (should fail at schema validation, verify compiler handles gracefully)
- Single clip filling entire timeline
- Two clips with identical start times on different tracks
- Gap between clips (no content for a time range)
- Clip trim offset for video assets
- Very short segments (sub-second)

---

## 10. Dependencies

### External Libraries
- editly: npm package (subprocess, not Python dependency)
- ffmpeg: system binary for poster generation

### Other Sessions
- **Depends on**: phase00-session01, phase00-session02, phase00-session03
- **Depended by**: phase00-session05-render-service-and-api-endpoints

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
