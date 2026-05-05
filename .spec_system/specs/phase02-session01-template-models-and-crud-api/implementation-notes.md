# Implementation Notes

**Session ID**: `phase02-session01-template-models-and-crud-api`
**Started**: 2026-05-05 06:24
**Last Updated**: 2026-05-05 06:35

---

## Session Progress

| Metric | Value |
|--------|-------|
| Tasks Completed | 20 / 20 |
| Estimated Remaining | 0 hours |
| Blockers | 0 |

---

## Task Log

### [2026-05-05] - Session Start

**Environment verified**:
- [x] Prerequisites confirmed (Phase 01 complete, 10 sessions done)
- [x] Tools available (Python 3.12, ruff, pytest)
- [x] Directory structure ready
- [x] SQLite dev database operational

---

### Task T001 - Verify prerequisites

**Started**: 2026-05-05 06:24
**Completed**: 2026-05-05 06:24
**Duration**: 1 minute

**Notes**:
- Confirmed all 10 Phase 0/1 sessions completed via state.json
- analyze-project.sh and check-prereqs.sh both pass
- SQLModel + aiosqlite operational with existing render pipeline

---

### Tasks T004/T005/T008 - Template SQLModel + ID generation

**Started**: 2026-05-05 06:25
**Completed**: 2026-05-05 06:26
**Duration**: 1 minute

**Notes**:
- Created Template and TemplateVersion SQLModel table classes
- ID generation follows existing base-36 pattern with tmpl_ and tver_ prefixes
- Initially used Relationship() for bidirectional ORM links but removed them due to SQLAlchemy mapper error with generic list types in async context
- All queries use explicit SELECTs instead of ORM lazy loading

**Files Changed**:
- `app/db/template_models.py` - New file: Template, TemplateVersion models + ID helpers

**BQC Fixes**:
- Contract alignment: Removed ORM Relationship declarations that caused mapper initialization failure in async contexts

---

### Tasks T006/T007 - Pydantic request/response schemas

**Started**: 2026-05-05 06:25
**Completed**: 2026-05-05 06:26
**Duration**: 1 minute

**Notes**:
- CreateTemplateRequest validates composition via existing Pydantic Composition model
- UpdateTemplateRequest has model_validator requiring at least one field
- TemplateVersionResponse stores composition as dict (JSON-parsed from DB string)
- TemplateListItem includes version_count for list display

**Files Changed**:
- `app/models/template.py` - New file: all request/response Pydantic models

---

### Task T002 - Alembic migration

**Started**: 2026-05-05 06:26
**Completed**: 2026-05-05 06:27
**Duration**: 1 minute

**Notes**:
- Migration 003: creates templates + template_versions tables
- Includes indexes on name, is_deleted, template_id
- Unique composite index on (template_id, version_number) prevents duplicate versions
- Full downgrade support

**Files Changed**:
- `alembic/versions/003_add_templates.py` - New migration file

---

### Task T003 - Register models in session

**Started**: 2026-05-05 06:27
**Completed**: 2026-05-05 06:27
**Duration**: 1 minute

**Notes**:
- Added import of app.db.template_models in session.py and alembic/env.py
- Ensures SQLModel.metadata.create_all picks up new tables

**Files Changed**:
- `app/db/session.py` - Added template_models import
- `alembic/env.py` - Added template_models import

---

### Tasks T009-T013 - Template CRUD layer

**Started**: 2026-05-05 06:27
**Completed**: 2026-05-05 06:29
**Duration**: 2 minutes

**Notes**:
- All CRUD functions follow render_crud.py patterns
- create_template: atomic template + version-1 creation in single commit
- update_template and soft_delete_template accept template_id (not object) to avoid SQLAlchemy expired-attribute issues in async context
- update_template re-fetches template from DB before modification to ensure fresh state
- list_templates excludes soft-deleted by default with deterministic DESC ordering
- soft_delete raises ValueError on already-deleted templates

**Files Changed**:
- `app/db/template_crud.py` - New file: create, get, list, update, soft_delete functions

**BQC Fixes**:
- State freshness: Changed update/delete CRUD to accept IDs and re-fetch from DB, preventing MissingGreenlet errors from expired SQLAlchemy object state in async sessions
- Trust boundary: All queries are parameterized via SQLModel select()
- Failure path: Explicit None returns and ValueError raises for not-found/invalid-state

---

### Task T014 - Template service layer

**Started**: 2026-05-05 06:29
**Completed**: 2026-05-05 06:30
**Duration**: 1 minute

**Notes**:
- TemplateService wraps CRUD with business validation
- Custom exception hierarchy: TemplateNotFoundError, TemplateDeletedError, TemplateAlreadyDeletedError
- Composition validated by Pydantic before serialization to JSON
- Structured logging on all mutation operations

**Files Changed**:
- `app/services/template_service.py` - New file: TemplateService class

---

### Task T015 - Template route handlers

**Started**: 2026-05-05 06:30
**Completed**: 2026-05-05 06:31
**Duration**: 1 minute

**Notes**:
- Five endpoints: POST, GET list, GET by ID, PUT, DELETE
- Thin handlers delegating to TemplateService
- Explicit error mapping: TemplateNotFoundError->404, TemplateDeletedError->409, TemplateAlreadyDeletedError->409
- List endpoint clamps limit to [1, 100] and offset to >=0
- All raise...from exc for proper exception chaining

**Files Changed**:
- `app/api/routes_templates.py` - New file: all five route handlers

---

### Task T016 - Wire router and deps

**Started**: 2026-05-05 06:31
**Completed**: 2026-05-05 06:31
**Duration**: 1 minute

**Notes**:
- Added TemplateServiceDep type alias to deps.py
- Registered template router in main.py under /v1 prefix
- Updated conftest.py to override template service in test client

**Files Changed**:
- `app/api/deps.py` - Added get_template_service and TemplateServiceDep
- `app/main.py` - Included templates_router
- `tests/conftest.py` - Added template service override in client fixture

---

### Tasks T017-T019 - Tests

**Started**: 2026-05-05 06:31
**Completed**: 2026-05-05 06:34
**Duration**: 3 minutes

**Notes**:
- 14 unit tests in test_template_crud.py covering all CRUD operations
- 26 integration/edge case tests in test_api_templates.py covering all endpoints
- Edge cases: version increment on multiple updates, soft-deleted excluded from list, pagination beyond total, duplicate names, large compositions, description-only update

**Files Changed**:
- `tests/test_template_crud.py` - New file: 14 CRUD unit tests
- `tests/test_api_templates.py` - New file: 26 integration + edge case tests

---

### Task T020 - Final validation

**Started**: 2026-05-05 06:34
**Completed**: 2026-05-05 06:35
**Duration**: 1 minute

**Notes**:
- Full test suite: 376 tests, all passing
- Ruff check: all files clean
- ASCII encoding: verified on all 8 new files

---

## Design Decisions

### Decision 1: ID-based CRUD instead of object-based

**Context**: SQLAlchemy objects become expired after async session commits, causing MissingGreenlet errors when attributes are accessed outside greenlet context
**Options Considered**:
1. Pass ORM objects between functions - simpler API but async-unsafe
2. Pass IDs and re-fetch inside each function - slightly more queries but async-safe

**Chosen**: Option 2
**Rationale**: Reliability in async context trumps minor query overhead. Re-fetching ensures fresh state and avoids subtle expired-attribute bugs.

### Decision 2: No ORM Relationship declarations

**Context**: SQLAlchemy mapper failed to initialize with generic list types in Relationship()
**Options Considered**:
1. Use Mapped[list[TemplateVersion]] annotation with relationship - requires additional SQLAlchemy imports
2. Remove relationships entirely, use explicit queries - simpler, no lazy-loading risks

**Chosen**: Option 2
**Rationale**: All queries are explicit SELECTs already. Relationships would only enable lazy loading which is problematic in async contexts anyway.

### Decision 3: Composition stored as Pydantic-serialized JSON

**Context**: Templates store composition as a JSON string in the database
**Options Considered**:
1. Store only the input fields (minimal) - loses Pydantic defaults
2. Store full Pydantic model_dump_json (with defaults) - larger but complete

**Chosen**: Option 2
**Rationale**: Stored composition includes all Pydantic defaults (e.g., fps=30, quality="medium"), making it self-describing and reproducible without needing the Pydantic schema to interpret.
