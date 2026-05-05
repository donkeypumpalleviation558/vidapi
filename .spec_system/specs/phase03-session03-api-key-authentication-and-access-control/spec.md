# Session Specification

**Session ID**: `phase03-session03-api-key-authentication-and-access-control`
**Phase**: 03 - Production Hardening
**Status**: Completed
**Created**: 2026-05-05

---

## 1. Session Overview

This session adds API key authentication and route-level access control for VidAPI's public API. The current service exposes render, template, artifact download, and poster endpoints without authentication, which leaves render access effectively bearer-by-ID. Phase 03 requires this gap to close before resource limits, operational endpoints, and a production stack are finalized.

The implementation keeps `/health` and `/v1/health` unauthenticated while protecting all non-health API routers with a shared FastAPI dependency. API keys are supplied through the `X-API-Key` header, validated against configured SHA-256 hashes, and never echoed in error payloads or logs. Authentication can be disabled explicitly for local development and tests, but production settings must reject unsafe auth configuration.

This session follows the existing thin-router and service-boundary patterns. Validation helpers live in `app/core/security.py`, FastAPI dependency wiring lives in the API layer, and route behavior is verified through integration tests that cover render, template, download, OpenAPI, and disabled-auth cases.

---

## 2. Objectives

1. Add configurable API key authentication with hashed key comparison and production safety validation.
2. Enforce authentication on render, template, download, and poster routes while leaving health routes public.
3. Return consistent 401 and 403 responses without leaking provided key material.
4. Document API key auth in OpenAPI and test enabled, disabled, missing, invalid, and valid key behavior.

---

## 3. Prerequisites

### Required Sessions
- [x] `phase03-session01-postgresql-persistence-and-alembic-migrations` - Provides stable database session behavior for protected route tests.
- [x] `phase03-session02-s3-compatible-storage-and-download-modes` - Provides current download and poster route behavior that auth must preserve.
- [x] `phase02-session01-template-models-and-crud-api` - Provides template CRUD routes to protect.
- [x] `phase02-session02-template-variables-and-rendering` - Provides template render route to protect.

### Required Tools/Knowledge
- FastAPI dependency injection and `fastapi.security.APIKeyHeader`.
- Pydantic settings validators and test-time settings cache isolation.
- SHA-256 hashing and constant-time comparison with `hmac.compare_digest`.
- Existing route test fixtures in `tests/conftest.py`.

### Environment Requirements
- Python 3.11+ environment with project dependencies installed through `uv`.
- Test database fixtures remain SQLite-backed for route tests.
- No external Redis, S3, Node, Editly, or FFmpeg services are required for the auth test subset.

---

## 4. Scope

### In Scope (MVP)
- Operator can enable API key authentication with configured SHA-256 key hashes - add settings, validation, and production guardrails.
- Client can pass an API key through `X-API-Key` - extract header with explicit missing and invalid error paths.
- System can protect render, template, download, and poster endpoints - apply the dependency at router boundaries.
- Operator can keep local development unauthenticated intentionally - preserve disabled-auth behavior through settings.
- API documentation can advertise the API key scheme - expose OpenAPI security metadata for protected routes.
- System can keep key material out of errors and logs - avoid echoing headers and add redaction-oriented tests.

### Out of Scope (Deferred)
- Database-backed key creation, rotation, or revocation - Reason: configured hashed key list satisfies Phase 03 MVP.
- Multi-tenant ownership checks for individual renders or templates - Reason: PRD excludes user accounts and billing.
- OAuth, JWT, sessions, or cookies - Reason: API key auth is the explicit Phase 03 scope.
- Fine-grained per-template or per-render authorization - Reason: this session establishes coarse API access control only.

---

## 5. Technical Approach

### Architecture

Add auth configuration to `Settings`, including an enable switch and a list of accepted SHA-256 API key hashes. Production validation should require auth to be enabled and at least one key hash to be configured. Development and test environments can explicitly disable auth to preserve current local ergonomics.

Implement pure validation helpers in `app/core/security.py`: normalize configured hashes, hash presented keys, compare with `hmac.compare_digest`, and redact known secret-bearing values for defensive logging paths. The helpers stay framework-independent so they can be unit-tested without FastAPI.

Add a FastAPI dependency in `app/api/auth.py` that reads `X-API-Key` via `APIKeyHeader(auto_error=False)`, checks `Settings`, and raises `HTTPException` with 401 for missing credentials and 403 for invalid credentials. Wire this dependency to non-health routers in `app/main.py` so future protected routers can follow the same pattern while health remains public.

### Design Patterns
- Router-level dependency: Applies access control at the boundary closest to public API resources.
- Pure helper functions: Keeps hash comparison and redaction easy to unit test.
- Constant-time comparison: Avoids timing leaks when comparing configured API key hashes.
- Settings validator guardrail: Prevents production startup with auth disabled or with no configured keys.

### Technology Stack
- Python 3.11+
- FastAPI 0.136.1 / Starlette 0.52.1
- Pydantic Settings
- pytest + pytest-asyncio + httpx ASGI transport

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/api/auth.py` | API key extraction and route dependency | ~80 |
| `tests/test_api_auth.py` | Route auth, OpenAPI, disabled mode, and secret-leak tests | ~220 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/core/config.py` | Add API key settings and production validation | ~35 |
| `app/core/security.py` | Replace placeholder with hash validation and redaction helpers | ~95 |
| `app/api/errors.py` | Add auth-related VidAPI error classes if needed by dependency | ~25 |
| `app/models/errors.py` | Add documented 401 and 403 response metadata | ~20 |
| `app/api/routes_renders.py` | Document 401/403 responses on protected render routes | ~20 |
| `app/api/routes_templates.py` | Document 401/403 responses on protected template routes | ~20 |
| `app/main.py` | Attach auth dependency to non-health routers and keep health public | ~15 |
| `tests/conftest.py` | Add auth fixture helpers and dependency cache reset if needed | ~30 |
| `tests/test_config.py` | Cover auth settings parsing and production validation | ~80 |
| `README.md` | Document local disabled mode and hashed API key configuration | ~45 |
| `docs/deployment.md` | Document production API key requirements | ~35 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] `/health` and `/v1/health` return successfully without API key headers.
- [ ] Missing `X-API-Key` returns 401 on non-health routes when auth is enabled.
- [ ] Invalid `X-API-Key` returns 403 on non-health routes when auth is enabled.
- [ ] Valid API keys can create, list, inspect, cancel, download, poster, template CRUD, and template-render requests.
- [ ] Auth can be disabled explicitly for local development and tests.
- [ ] OpenAPI includes an API key security scheme and protected operations reference it.
- [ ] API key values do not appear in error payloads, structured error context, or documented examples.

### Testing Requirements
- [ ] Unit tests written and passing for security helpers.
- [ ] Integration tests written and passing for protected route groups.
- [ ] Configuration tests written and passing for development/test/production behavior.
- [ ] Manual OpenAPI inspection completed for security scheme visibility.

### Non-Functional Requirements
- [ ] Non-render API endpoints remain within the PRD target of under 200 ms p95 under normal single-node load.
- [ ] Authentication checks avoid database access and external network calls.
- [ ] Hash comparisons use constant-time comparison.

### Quality Gates
- [ ] All files ASCII-encoded.
- [ ] Unix LF line endings.
- [ ] Code follows project conventions.

---

## 8. Implementation Notes

### Key Considerations
- Keep `/v1/health` public even if it depends on DB and Redis checks.
- Prefer SHA-256 hash configuration over plaintext API key configuration.
- Keep route handlers thin by attaching auth at router inclusion or router definition time.
- Update documentation with a small shell example for generating a SHA-256 hash.
- Preserve existing tests by defaulting test settings to auth disabled unless a test explicitly enables auth.

### Potential Challenges
- OpenAPI security metadata can be lost if auth is wrapped incorrectly: Use `APIKeyHeader` through `Security` or a dependency shape that FastAPI can document.
- Settings cache mutation can contaminate tests: Reuse the existing `reset_settings_cache` and dependency cache clear pattern.
- Adding router-level dependencies may change validation ordering: Auth tests should use representative valid requests and assert missing credentials are handled before business logic.
- Secret redaction is easy to miss in failure paths: Do not include header values in exception details, log context, or test failure messages.

### Relevant Considerations
- [P00] **No authentication**: This is the direct Phase 03 mitigation; all non-health route groups become API-key protected.
- [P02] **ID-based CRUD re-fetching**: Keep existing route behavior intact and avoid passing ORM objects across auth or service boundaries.
- [P01] **Settings singleton mutation in tests**: Auth tests must isolate environment overrides and reset cached settings/dependencies.
- [P02] **structlog event naming**: If auth logging is added, avoid reserved `event` fields and never include secret header values.

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Protected endpoints accidentally remain reachable because the dependency is not attached to every non-health router.
- Missing and invalid API keys collapse into inconsistent response formats or leak provided key values.
- Test settings or app dependency overrides leave auth enabled or disabled across unrelated tests.

---

## 9. Testing Strategy

### Unit Tests
- Test SHA-256 key hashing and constant-time hash validation in `app/core/security.py`.
- Test invalid configured hash values are rejected or ignored according to the chosen helper contract.
- Test redaction helpers remove `X-API-Key`, `Authorization`, and key-like fields from simple dictionaries.

### Integration Tests
- Test `/health` and `/v1/health` remain unauthenticated when auth is enabled.
- Parameterize render and template routes for missing, invalid, and valid `X-API-Key` cases.
- Test download and poster endpoints require auth before artifact lookup.
- Test OpenAPI exposes `X-API-Key` security metadata for protected paths and not for health.

### Manual Testing
- Start the app with auth enabled and one generated key hash, then verify a protected request fails without `X-API-Key` and succeeds with the raw key.
- Inspect `/openapi.json` or `/docs` to confirm the API key auth scheme appears.

### Edge Cases
- Empty, whitespace-only, and duplicate configured hashes.
- Empty or whitespace-only API key header.
- Production environment with auth disabled.
- Production environment with auth enabled but no key hashes.
- Valid key for POST endpoints still preserves existing 202/201 behavior.

---

## 10. Dependencies

### External Libraries
- No new runtime dependencies required.
- Existing FastAPI security helpers are sufficient.

### Other Sessions
- **Depends on**: `phase03-session01-postgresql-persistence-and-alembic-migrations`, `phase03-session02-s3-compatible-storage-and-download-modes`
- **Depended by**: `phase03-session04-limits-resource-controls-and-asset-security-hardening`, `phase03-session05-operational-visibility-and-production-stack`

---

## Next Steps

Session complete. Run the validate workflow step if additional verification is needed.
