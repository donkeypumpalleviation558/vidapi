# Considerations

> Institutional memory for AI assistants. Updated between phases via carryforward.
> **Line budget**: 600 max | **Last updated**: Phase 03 (2026-05-05)

---

## Active Concerns

Items requiring attention in upcoming phases. Review before each session.

### Technical Debt
<!-- Max 5 items -->

- [P03] **Migration-managed schema startup**: Production now depends on Alembic and explicit metadata alignment. Any new table or model must update both runtime metadata and migrations or startup will fail closed.
- [P03] **Single API-key auth model**: Route-level API keys are enough for self-hosted access, but not for future per-user or multi-tenant authorization.

### External Dependencies
<!-- Max 5 items -->

- [P03] **S3 and URL mode drift**: Storage backend, public/signed/proxy URL mode, and webhook URLs all depend on consistent deployment settings. Misconfiguration can break downloads or expose artifacts.
- [P03] **Redis auth and transport expectations**: Production compose and health checks now support authenticated Redis URLs, but non-compose deployments still need explicit password and TLS enforcement.

### Performance / Security
<!-- Max 5 items -->

- [P03] **Guardrail tuning is deployment-specific**: Body size, composition, queue depth, asset limits, and worker cleanup intervals are bounded now, but operators still need sane per-environment values.
- [P03] **Redaction discipline**: Ops endpoints and logs are bounded and redacted, but any future observability expansion must preserve the same secret handling rules.

### Architecture
<!-- Max 5 items -->

- [P03] **Centralized artifact URL resolution**: Keep one resolver for local, proxy, signed, and public artifact URLs so routes and webhook payloads stay aligned.
- [P03] **Thin read-only ops routes**: Keep aggregate logic in services or CRUD helpers to avoid redaction drift in route handlers.

---

## Lessons Learned

Proven patterns and anti-patterns. Reference during implementation.

### What Worked
<!-- Max 15 items -->

- [P03] **Fail-closed production startup**: Requiring validated config and satisfied migrations is safer than silently creating schema at boot.
- [P03] **Config-driven backend selection**: One settings layer for DB, storage, auth, and limits keeps local and production behavior predictable.
- [P03] **Centralized artifact URL resolution**: A single resolver prevents drift between downloads, posters, and webhook payloads.
- [P03] **Bounded observability**: Authenticated ops endpoints plus redacted structured logs expose enough context without leaking payloads.
- [P03] **Worker startup cleanup**: Pruning inactive workspaces on boot keeps orphan cleanup deterministic.
- [P03] **Full Redis URL health checks**: Using the full configured URL is simpler and safer than shell-parsing host and port.
- [P03] **API key hashes only**: Store hashes, not raw keys, and keep `/health` public.
- [P02] **Pure-function segment compiler**: Stateless compiler functions are easier to test and compose than class-based alternatives.
- [P02] **Discriminated unions for asset types**: Pydantic type discrimination on a `type` literal gives clean validation and serialization.
- [P02] **Atomic file writes (tmp + rename)**: Prevents corrupted artifacts. The same pattern held for audio intermediates.
- [P02] **Manual redirect following for SSRF**: Per-hop validation prevents redirect-to-private-IP bypass attacks.
- [P02] **Replay metadata (`replay.json`)**: Capturing command, args, and env makes subprocess failures reproducible.
- [P02] **Content-addressed SHA-256 asset cache**: Avoids redundant downloads across renders.
- [P01] **Worker drives status transitions externally**: RenderService stays stateless while the worker owns transitions and cancellation checkpoints.
- [P01] **Cooperative cancellation via DB flag**: Renderer-agnostic and race-safe across queue backends.

### What to Avoid
<!-- Max 10 items -->

- [P03] **Implicit schema creation in production**: It hides drift and makes rollbacks harder.
- [P03] **Duplicating storage URL logic across routes**: It causes inconsistencies in downloads and webhook payloads.
- [P03] **Raw secrets in responses or logs**: Redaction must stay centralized and test-covered.
- [P03] **Parsing Redis host and port in shell health checks**: It is fragile compared with using the configured URL directly.
- [P02] **MoviePy wrapper**: It hides the filter graph control needed for precise timing.
- [P02] **Synchronous rendering in API process**: It blocks the event loop. Always use workers.
- [P02] **Import-time DB engine creation**: It blocks test overrides. Use lazy initialization.
- [P01] **ARQ `@staticmethod` for `redis_settings`**: ARQ 0.28.0 expects attribute access. Use class attribute assignment.
- [P01] **`proc.communicate()` for long renders**: It buffers all output. Use line-by-line stderr streaming for progress and cancel checks.
- [P01] **Settings singleton mutation in tests**: It causes cross-test contamination. Create isolated Settings instances.

### Tool/Library Notes
<!-- Max 5 items -->

- [P03] **`asyncpg`**: Works cleanly as the PostgreSQL async driver behind the settings-driven DB path.
- [P03] **Prometheus text snapshots**: Plain text metrics output is enough for single-node API and worker visibility without adding a registry dependency.
- [P02] **Jinja2 SandboxedEnvironment + StrictUndefined**: Safe defaults for user-provided template variables.
- [P02] **FastAPI 0.136.1 / Starlette 0.52.1**: This pairing clears the Phase 02 CVE floor while preserving compatibility.
- [P02] **structlog event naming**: `ainfo` and `awarning` reserve `event`; use a different key such as `webhook_event`.

---

## Resolved

Recently closed items (buffer - rotates out after 2 phases).

| Phase | Item | Resolution |
|-------|------|------------|
| P03 | No API auth on non-health routes | Added API-key auth for render, template, and ops routes while keeping health endpoints public.
| P03 | Orphaned workspace accumulation | Worker startup now prunes inactive workspaces and keeps cleanup bounded.
| P03 | Implicit schema creation in production | Startup now requires migration readiness instead of mutating schema on boot.
| P03 | Unbounded request and queue exposure | Request size, composition, asset, and queue guardrails now fail closed.
| P03 | Redis health probe host parsing | Worker health checks now use the configured Redis URL directly.
| P02 | No rate limiting on `POST /v1/renders` | Added bounded rate limiting and structured 429 responses in Phase 02.
| P02 | Wildcard production CORS | Phase 02 now rejects wildcard origins outside debug mode.
| P02 | Starlette CVE backlog | Upgraded FastAPI and raised the Starlette floor to `>=0.49.1`.
| P01 | Synchronous render in POST handler | ARQ async worker pipeline with `RENDER_MODE` toggle.
| P01 | No render workspace cleanup | WorkspaceManager with configurable cleanup on success/failure.

---

*Auto-generated by carryforward. Manual edits allowed but may be overwritten.*
