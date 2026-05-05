# Task Checklist

**Session ID**: `phase03-session03-api-key-authentication-and-access-control`
**Total Tasks**: 18
**Estimated Duration**: 3-4 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[SNNMM]` = Session reference (NN=phase number, MM=session number)
- `TNNN` = Task ID

---

## Progress Summary

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| Setup | 3 | 3 | 0 |
| Foundation | 5 | 5 | 0 |
| Implementation | 7 | 7 | 0 |
| Testing | 3 | 3 | 0 |
| **Total** | **18** | **18** | **0** |

---

## Setup (3 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0303] Verify auth prerequisites and current public route coverage in render, template, download, poster, and health routes (`app/main.py`)
- [x] T002 [S0303] Create the auth dependency module and test scaffold with route fixtures ready for enabled and disabled modes (`app/api/auth.py`)
- [x] T003 [S0303] Review existing settings cache reset paths for auth test isolation without cross-test contamination (`tests/conftest.py`)

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T004 [S0303] Add API key auth settings, configured SHA-256 hash list, and production validators with explicit failure messages (`app/core/config.py`)
- [x] T005 [S0303] Implement API key hashing, configured hash normalization, and constant-time validation helpers (`app/core/security.py`)
- [x] T006 [S0303] Implement secret redaction helpers for key-bearing headers and fields without mutating caller data (`app/core/security.py`)
- [x] T007 [S0303] [P] Add documented 401 and 403 auth response metadata for route OpenAPI definitions (`app/models/errors.py`)
- [x] T008 [S0303] [P] Add auth error classes or response helpers for missing and invalid credentials with no secret echoing (`app/api/errors.py`)

---

## Implementation (7 tasks)

Main feature implementation.

- [x] T009 [S0303] Implement `require_api_key` FastAPI dependency using `X-API-Key` with schema-validated input and explicit error mapping (`app/api/auth.py`)
- [x] T010 [S0303] Wire API key auth onto render routes with authorization enforced at the router boundary closest to the resource (`app/main.py`)
- [x] T011 [S0303] Wire API key auth onto template routes with authorization enforced at the router boundary closest to the resource (`app/main.py`)
- [x] T012 [S0303] Preserve unauthenticated root and versioned health routes while keeping DB and Redis health behavior unchanged (`app/main.py`)
- [x] T013 [S0303] Document 401 and 403 auth responses on render, cancel, status, download, poster, and list endpoints (`app/api/routes_renders.py`)
- [x] T014 [S0303] Document 401 and 403 auth responses on template CRUD and template render endpoints (`app/api/routes_templates.py`)
- [x] T015 [S0303] Update README and deployment docs with hash generation, local disabled mode, and production auth requirements (`README.md`, `docs/deployment.md`)

---

## Testing (3 tasks)

Verification and quality assurance.

- [x] T016 [S0303] [P] Write unit and configuration tests for hash validation, redaction, disabled mode, and unsafe production settings (`tests/test_config.py`)
- [x] T017 [S0303] Write integration tests for health public access and render/template/download/poster auth flows with missing, invalid, and valid keys (`tests/test_api_auth.py`)
- [x] T018 [S0303] Run targeted tests, verify OpenAPI security metadata, and validate ASCII encoding on changed files (`tests/test_api_auth.py`)

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

Run the validate workflow step to verify session completeness.
