# Task Checklist

**Session ID**: `phase00-session04-editly-renderer-and-segment-compiler`
**Total Tasks**: 22
**Estimated Duration**: 3-4 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0004]` = Session reference (Phase 00, Session 04)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 3 | 3 | 0 |
| Foundation | 5 | 5 | 0 |
| Implementation | 9 | 9 | 0 |
| Testing | 5 | 5 | 0 |
| **Total** | **22** | **22** | **0** |

---

## Setup (3 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0004] Verify prerequisites met -- confirm Pydantic composition models, storage protocol, asset service, and DB render model exist from Sessions 01-03
- [x] T002 [S0004] Add Editly and poster configuration settings to Settings (`app/core/config.py`)
- [x] T003 [S0004] Create renderer directory exports (`app/renderers/__init__.py`)

---

## Foundation (5 tasks)

Core protocol, dataclasses, and segment compiler algorithm.

- [x] T004 [S0004] Define Renderer protocol with `compile()` and `render()` methods, plus CompiledRender and RenderArtifact frozen dataclasses (`app/renderers/base.py`)
- [x] T005 [S0004] Implement segment boundary collector -- walk all clips, collect `start` and `start + length` boundaries, add timeline 0 and total duration, sort and deduplicate with epsilon tolerance (`app/renderers/editly.py`)
- [x] T006 [S0004] Implement segment generator -- convert sorted boundaries into non-overlapping time segments, each with its list of active clips resolved by time overlap (`app/renderers/editly.py`)
- [x] T007 [S0004] Implement VidAPI-to-Editly layer mapper for video assets -- translate src to local path, fit mode to resizeMode, compute cutFrom/cutTo from clip-relative timing (`app/renderers/editly.py`)
- [x] T008 [S0004] [P] Implement VidAPI-to-Editly layer mapper for image and text PNG assets -- image as `image-overlay` layer with path and resizeMode, text uses pre-rendered PNG path (`app/renderers/editly.py`)

---

## Implementation (9 tasks)

Main feature implementation.

- [x] T009 [S0004] [P] Implement VidAPI-to-Editly layer mapper for color assets -- solid fill as background layer or fill-color (`app/renderers/editly.py`)
- [x] T010 [S0004] Implement soundtrack and audio mapping -- translate timeline.soundtrack to Editly top-level audioTracks with volume and effect handling (`app/renderers/editly.py`)
- [x] T011 [S0004] Implement full Editly spec assembler -- combine segments into Editly clips array, set top-level width/height/fps/outPath, attach audioTracks, serialize as deterministic JSON with sort_keys (`app/renderers/editly.py`)
- [x] T012 [S0004] Implement `EditlyRenderer.compile()` -- orchestrate boundary collection, segment generation, layer mapping, spec assembly, and write compiled.editly.json + replay.json to workspace with cleanup on scope exit for all acquired resources (`app/renderers/editly.py`)
- [x] T013 [S0004] Implement replay metadata generation -- capture Editly executable path, args, environment variables, input/output paths, timeout, and timestamp into replay.json (`app/renderers/editly.py`)
- [x] T014 [S0004] Implement `EditlyRenderer.render()` -- invoke Editly as Node subprocess via `asyncio.create_subprocess_exec` with timeout, retry/backoff, and failure-path handling; capture full stderr; check exit code; verify output file exists (`app/renderers/editly.py`)
- [x] T015 [S0004] Implement render error classification -- map non-zero exit codes, timeout, missing output, and invalid output to structured error codes and messages (`app/renderers/editly.py`)
- [x] T016 [S0004] Implement poster generation via FFmpeg frame extraction -- extract frame at configurable timestamp from rendered output, save as poster.jpg with timeout, retry/backoff, and failure-path handling (`app/renderers/poster.py`)
- [x] T017 [S0004] Wire EditlyRenderer into renderer registry/factory -- resolve renderer choice from Composition.renderer field, default to editly for MVP (`app/renderers/__init__.py`)

---

## Testing (5 tasks)

Verification and quality assurance.

- [x] T018 [S0004] [P] Write segment compiler unit tests -- single clip, two sequential clips, overlapping clips on different tracks, gap between clips, text overlay active for partial background, track z-order preservation, sub-second segments (`tests/test_segment_compiler.py`)
- [x] T019 [S0004] [P] Write Editly layer mapper unit tests -- video asset mapping with cutFrom/cutTo, image asset mapping, text PNG overlay mapping, color asset mapping, fit mode translation for cover/contain/stretch (`tests/test_editly_compiler.py`)
- [x] T020 [S0004] [P] Write Editly full compile integration tests -- compose a representative Composition with image background + text overlay + soundtrack, verify compiled JSON structure, verify deterministic output, verify replay.json contents (`tests/test_editly_compiler.py`)
- [x] T021 [S0004] [P] Write poster generation tests -- verify FFmpeg command construction, handle missing ffmpeg gracefully, verify timeout behavior (`tests/test_poster.py`)
- [x] T022 [S0004] Run full test suite and verify all tests pass, validate ASCII encoding on all new files

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
