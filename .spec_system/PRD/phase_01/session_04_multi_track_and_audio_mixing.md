# Session 04: Multi-track and Audio Mixing

**Session ID**: `phase01-session04-multi-track-and-audio-mixing`
**Status**: Not Started
**Estimated Tasks**: ~20
**Estimated Duration**: 2-4 hours

---

## Objective

Extend the segment compiler and Editly renderer to support multi-track compositing with correct z-order by track index, and implement soundtrack and detached audio clip mixing.

---

## Scope

### In Scope (MVP)
- Multi-track segment compiler: overlapping clips from different tracks
- Z-order by track index (track 0 = bottom, higher index = on top)
- Segment compiler generates layers per segment from multiple active tracks
- Editly layer mapper handles multiple layers per clip
- Soundtrack audio mixing in final output
- Detached audio clips (audio assets on tracks with timing)
- Audio volume control per clip and soundtrack
- Audio trim (cutFrom/cutTo equivalent)
- FFmpeg audio mixing for multi-source audio
- Tests for multi-track segment generation, z-order, and audio mixing

### Out of Scope
- Advanced audio ducking
- Crossfade transitions between clips
- Complex transition effects
- Docker Compose (session 05)

---

## Prerequisites

- [ ] Session 02 complete (worker render pipeline stable)
- [ ] Existing segment compiler passes all Phase 00 tests

---

## Deliverables

1. Multi-track segment compiler supporting overlapping clips
2. Z-order layer generation from track indices
3. Editly layer mapper for multi-layer segments
4. Soundtrack mixing implementation
5. Detached audio clip support with volume and trim
6. FFmpeg audio mixing for combined output
7. Tests covering multi-track scenarios and audio mixing

---

## Success Criteria

- [ ] Multi-track compositions render with correct z-order (higher track index on top)
- [ ] Overlapping clips from different tracks produce correct layered segments
- [ ] Soundtrack plays behind video/image content at specified volume
- [ ] Detached audio clips play at specified timeline positions
- [ ] Audio trim and volume controls work correctly
- [ ] Existing single-track tests continue to pass
