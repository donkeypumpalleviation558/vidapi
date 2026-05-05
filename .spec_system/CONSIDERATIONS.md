# Considerations

> Institutional memory for AI assistants. Updated between phases via carryforward.
> **Line budget**: 600 max | **Last updated**: Phase 00 (2026-05-05)

---

## Active Concerns

Items requiring attention in upcoming phases. Review before each session.

### Technical Debt
<!-- Max 5 items -->

- [P00] **Synchronous render in POST handler**: Render executes inline in the request handler, blocking the event loop. Must migrate to async worker (ARQ) in Phase 01.
- [P00] **Base-36 render IDs**: Custom ID generation is sortable but non-standard. Migrate to python-ulid library in Phase 03 production hardening.
- [P00] **No render workspace cleanup**: Ephemeral render workspaces and logs accumulate on disk. Need cleanup policy or TTL-based pruning.
- [P00] **No rate limiting on POST /v1/renders**: Unbounded render submissions risk resource exhaustion. Add rate limiting in Phase 01.

### External Dependencies
<!-- Max 5 items -->

- [P00] **FFmpeg 6+**: Must be available in all environments. Docker handles this, but local dev needs manual install.
- [P00] **Redis for ARQ job queue**: Required for async workers even in dev mode.
- [P00] **Editly Node.js binary**: Must be installed and on PATH. Binary availability is not validated at app startup -- a missing binary only surfaces at render time.
- [P00] **Font availability**: Inter/Roboto/Noto Sans must be installed. Font search paths are configurable but presence is not verified at startup.

### Performance / Security
<!-- Max 5 items -->

- [P00] **FFmpeg subprocess resource limits**: No memory, CPU time, or disk limits on spawned FFmpeg/Editly processes. Abuse vector for DoS.
- [P00] **Remote asset fetch limits**: Timeouts and size limits are configured but not battle-tested under load.
- [P00] **CORS wildcard origins**: Default allowed_origins is ["*"]. Must restrict to specific domains for production.
- [P00] **No authentication**: Renders are accessible to anyone with the render_id. Scope to authenticated users in Phase 03.

### Architecture
<!-- Max 5 items -->

- [P00] **FFmpeg filter graph complexity**: Scales non-linearly with track/clip count. May need chunked rendering for complex compositions.
- [P00] **Text rendering via Pillow**: Limited typography compared to browser-based rendering. May need Playwright path for `html` asset type later.
- [P00] **Single renderer implemented**: Renderer protocol is established but only Editly exists. Future renderers (FFmpeg-direct, Remotion) must conform to the protocol.

---

## Lessons Learned

Proven patterns and anti-patterns. Reference during implementation.

### What Worked
<!-- Max 15 items -->

- [P00] **Pure-function segment compiler**: Stateless functions (collect_boundaries, generate_segments) are easier to test and compose than class-based alternatives.
- [P00] **Discriminated unions for asset types**: Pydantic v2 type discrimination on `type` literal field gives clean validation and serialization for 5+ asset types.
- [P00] **Atomic file writes (tmp + rename)**: Prevents corrupted artifacts from crashes. Used in both storage adapter and asset cache.
- [P00] **Manual redirect following for SSRF**: Per-hop SSRF validation prevents redirect-to-private-IP bypass attacks that automated redirect following misses.
- [P00] **Epsilon tolerance (1e-6) for boundary dedup**: Eliminates micro-gap segments caused by floating-point arithmetic in timeline calculations.
- [P00] **Non-fatal poster generation**: PosterError is logged as warning and does not fail an otherwise successful render.
- [P00] **Replay metadata (replay.json)**: Captures exact command, args, env, and paths for reproducing subprocess failures outside the app.
- [P00] **Lazy engine init with set_engine()**: Avoids import-time side effects and enables clean DB overrides in tests.
- [P00] **Content-addressed SHA-256 asset cache**: Avoids redundant downloads for repeated assets across renders.
- [P00] **Track z-order: index 0 = bottom**: Matches natural reading order and Editly layer ordering. Higher track indices render on top.

### What to Avoid
<!-- Max 10 items -->

- [P00] **MoviePy wrapper**: Abstracts away filter graph control needed for precise timing and multi-track composition.
- [P00] **Synchronous rendering in API process**: Blocks the event loop. Always run renders in a worker or background task.
- [P00] **Import-time DB engine creation**: Blocks test overrides and causes module coupling. Use lazy initialization instead.

### Tool/Library Notes
<!-- Max 5 items -->

- [P00] **uv for dependency management**: Significantly faster than pip, handles PEP 668 cleanly. Use over pip for all installs.
- [P00] **Editly allowRemoteRequests: false**: Prevents Editly from fetching URLs independently. All fetching goes through VidAPI's SSRF-validated asset service.
- [P00] **hatchling build backend**: Lightweight with explicit package discovery via tool.hatch.build.targets.wheel.packages. Avoids setuptools auto-discovery issues.

---

## Resolved

Recently closed items (buffer - rotates out after 2 phases).

| Phase | Item | Resolution |
|-------|------|------------|
| - | *No resolved items yet* | - |

---

*Auto-generated by carryforward. Manual edits allowed but may be overwritten.*
