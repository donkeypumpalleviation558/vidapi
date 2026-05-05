# Considerations

> Institutional memory for AI assistants. Updated between phases via carryforward.
> **Line budget**: 600 max | **Last updated**: Phase 01 (2026-05-05)

---

## Active Concerns

Items requiring attention in upcoming phases. Review before each session.

### Technical Debt
<!-- Max 5 items -->

- [P00] **Base-36 render IDs**: Custom ID generation is sortable but non-standard. Migrate to python-ulid library in Phase 03 production hardening.
- [P01] **TTL-based workspace cleanup**: Orphaned workspaces from crashed workers accumulate indefinitely. WorkspaceManager handles happy-path cleanup but has no periodic scan for orphans.
- [P01] **No rate limiting on POST /v1/renders**: Unbounded render submissions risk resource exhaustion. A rate_limit.py file exists but is not wired into routes.
- [P01] **Starlette CVE backlog**: CVE-2025-54121 and CVE-2025-62727 pre-date Phase 01. Upgrade starlette >= 0.49.1 in next maintenance pass.

### External Dependencies
<!-- Max 5 items -->

- [P01] **ARQ version sensitivity**: 0.28.0 changed redis_settings from callable to attribute access. Pin or document expected API contract to avoid surprise breakage on upgrade.
- [P01] **Editly headless GL in Docker**: Requires Xvfb + GL runtime libs (libgl1, libegl1, libxi6, libgles2). Worker entrypoint must start Xvfb before ARQ.
- [P00] **Editly Node.js binary on PATH**: Local dev still requires manual install. Binary availability not validated at startup -- surfaces only at render time.
- [P00] **Font availability**: Inter/Roboto/Noto Sans must be installed. Presence not verified at startup.

### Performance / Security
<!-- Max 5 items -->

- [P00] **FFmpeg subprocess resource limits**: No memory, CPU time, or disk limits on spawned processes. Abuse vector for DoS.
- [P00] **CORS wildcard origins**: Default allowed_origins is ["*"]. Must restrict for production.
- [P00] **No authentication**: Renders accessible to anyone with the render_id. Scope to authenticated users in Phase 03.
- [P01] **Redis connection TLS not enforced**: REDIS_URL supports rediss:// but no production guidance or validation exists.
- [P01] **Redis AUTH not configured**: Docker Redis runs without a password. Production must require authentication.

### Architecture
<!-- Max 5 items -->

- [P00] **FFmpeg filter graph complexity**: Scales non-linearly with track/clip count. May need chunked rendering for complex compositions.
- [P00] **Text rendering via Pillow**: Limited typography. May need Playwright path for html asset type later.
- [P00] **Single renderer implemented**: Only Editly exists. Future renderers must conform to the protocol.
- [P01] **Two-pass audio overhead**: Video copy + FFmpeg audio mix adds I/O proportional to output file size. Acceptable for MVP but may need single-pass for large outputs.
- [P01] **No WebSocket/SSE progress streaming**: Polling is sufficient for MVP. Real-time UIs will need push-based progress.

---

## Lessons Learned

Proven patterns and anti-patterns. Reference during implementation.

### What Worked
<!-- Max 15 items -->

- [P00] **Pure-function segment compiler**: Stateless functions are easier to test and compose than class-based alternatives. Same pattern applied successfully to audio mixing in P01.
- [P00] **Discriminated unions for asset types**: Pydantic v2 type discrimination on `type` literal field gives clean validation and serialization.
- [P00] **Atomic file writes (tmp + rename)**: Prevents corrupted artifacts. Extended in P01 for audio intermediate files.
- [P00] **Manual redirect following for SSRF**: Per-hop validation prevents redirect-to-private-IP bypass attacks.
- [P00] **Replay metadata (replay.json)**: Exact command, args, env for reproducing subprocess failures.
- [P00] **Content-addressed SHA-256 asset cache**: Avoids redundant downloads across renders.
- [P01] **Worker drives status transitions externally**: RenderService exposes stateless stage methods; worker controls transitions. Enables progress tracking and cancellation checkpoints between stages.
- [P01] **Cooperative cancellation via DB flag**: Renderer-agnostic, testable, handles race conditions naturally via state machine. Works regardless of queue backend.
- [P01] **Rate-limited progress updates (2% + 2s)**: Prevents DB write storms during fast renders while remaining responsive for UIs.
- [P01] **Persist input.json before enqueue**: Avoids msgpack serialization issues with Pydantic models. Worker reads from workspace, consistent with existing patterns.
- [P01] **Conditional audio path**: Editly audioTracks for soundtrack-only (zero regression), FFmpeg post-processing only when detached audio clips exist.
- [P01] **Custom worker-entrypoint.sh**: Starts Xvfb in background with signal trapping for proper cleanup. More reliable than xvfb-run wrapper.
- [P01] **Best-effort progress parsing**: Never raises. FFmpeg output format varies across versions -- silently skip unparseable lines.

### What to Avoid
<!-- Max 10 items -->

- [P00] **MoviePy wrapper**: Abstracts away filter graph control needed for precise timing.
- [P00] **Synchronous rendering in API process**: Blocks the event loop. Always use workers.
- [P00] **Import-time DB engine creation**: Blocks test overrides. Use lazy initialization.
- [P01] **ARQ @staticmethod for redis_settings**: ARQ 0.28.0 expects attribute access. Use class attribute assignment.
- [P01] **proc.communicate() for long renders**: Buffers all output -- use line-by-line stderr streaming for progress and cancel checks.
- [P01] **Settings singleton mutation in tests**: Causes cross-test contamination. Create isolated Settings instances per test case.
- [P01] **xvfb-run in Docker CMD**: Unreliable process management. Use background Xvfb with explicit signal trapping.

### Tool/Library Notes
<!-- Max 5 items -->

- [P00] **uv for dependency management**: Faster than pip, handles PEP 668 cleanly.
- [P00] **Editly allowRemoteRequests: false**: All fetching goes through VidAPI's SSRF-validated asset service.
- [P01] **ARQ 0.28.0**: redis_settings must be class attribute; max_tries=1 prevents retry storms; job_timeout should be dynamic (settings + buffer).
- [P01] **FFmpeg -c:v copy for audio post-processing**: Fast audio mixing without video re-encoding. Requires intermediate file + atomic rename.
- [P01] **Docker multi-stage with node-gyp**: Needs python3 symlink and build-essential in the node stage for native module compilation.

---

## Resolved

Recently closed items (buffer - rotates out after 2 phases).

| Phase | Item | Resolution |
|-------|------|------------|
| P01 | Synchronous render in POST handler | ARQ async worker pipeline with RENDER_MODE toggle |
| P01 | No render workspace cleanup | WorkspaceManager with configurable cleanup on success/failure |
| P01 | Redis for ARQ job queue | Docker Compose Redis service + pool lifecycle in FastAPI lifespan |

---

*Auto-generated by carryforward. Manual edits allowed but may be overwritten.*
