# Session Specification

**Session ID**: `phase02-session01-template-models-and-crud-api`
**Phase**: 02 - Templates and Polish
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session builds the template persistence layer and full CRUD API that enables clients to create, list, retrieve, update, and soft-delete reusable composition templates. Templates are the core abstraction that makes VidAPI useful for repeatable programmatic video generation -- without them, every render requires a full composition payload.

The session introduces two new database tables (templates and template_versions), a template service layer following the same patterns established in Phase 0/1 render services, and five REST endpoints under `/v1/templates`. Template versioning is immutable: updates create new version rows rather than mutating existing composition data, preserving historical render reproducibility.

This session deliberately excludes variable substitution, the template render endpoint, and webhook delivery -- those depend on the CRUD foundation built here and are handled in Sessions 02 and 03.

---

## 2. Objectives

1. Implement Template and TemplateVersion SQLModel database models with proper relationships
2. Build a template service layer with create, list, get, update, and soft-delete operations
3. Deliver five CRUD API endpoints matching the canonical public API contract in the PRD
4. Ensure composition JSON is validated via existing Pydantic models on create and update
5. Support paginated template listing with soft-delete filtering

---

## 3. Prerequisites

### Required Sessions
- [x] `phase01-session05-docker-compose-stack` - Provides working async pipeline and DB layer

### Required Tools/Knowledge
- SQLModel ORM patterns (established in app/db/models.py and render_crud.py)
- FastAPI route patterns (established in app/api/routes_renders.py)
- Pydantic v2 model design

### Environment Requirements
- Python 3.11+ with project dependencies installed
- SQLite dev database operational

---

## 4. Scope

### In Scope (MVP)
- Template model with id, name, description, composition JSON, variable schema, active_version_id, is_deleted, timestamps - implementing full CRUD persistence
- TemplateVersion model with id, template_id, version number, composition JSON, variable schema, created_at - immutable version storage
- Template CRUD service with create/list/get/update/delete operations - business logic separated from routes
- POST /v1/templates endpoint - create template with initial version
- GET /v1/templates endpoint - paginated list excluding soft-deleted
- GET /v1/templates/{id} endpoint - retrieve with active version composition
- PUT /v1/templates/{id} endpoint - update creating new immutable version
- DELETE /v1/templates/{id} endpoint - soft-delete without data loss
- Pydantic request/response models for all template operations
- Composition validation on create and update using existing Composition model
- Alembic migration for new tables

### Out of Scope (Deferred)
- Template variable substitution and Jinja2 engine - *Reason: Session 02*
- POST /v1/templates/{id}/renders endpoint - *Reason: Session 02*
- Webhook delivery on template renders - *Reason: Session 03*
- Rate limiting on template endpoints - *Reason: already scaffolded but wiring is Phase 03*

---

## 5. Technical Approach

### Architecture
Follow the established layered pattern: route handlers -> service layer -> CRUD functions -> SQLModel. Templates use the same async session management and dependency injection patterns as renders.

### Design Patterns
- **Immutable versioning**: Updates never mutate existing version rows; new version created and active pointer updated atomically
- **Soft delete**: is_deleted flag with exclusion from list queries by default
- **Service layer separation**: Route handlers remain thin; business logic in template_service.py
- **Dependency injection**: TemplateService provided via FastAPI Depends()

### Technology Stack
- SQLModel 0.0.24 (ORM and table models)
- FastAPI 0.115.12 (route handlers)
- Pydantic 2.11.2 (request/response schemas)
- Alembic (migration)
- aiosqlite (async SQLite driver)

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/db/template_models.py` | Template and TemplateVersion SQLModel tables | ~80 |
| `app/db/template_crud.py` | Database CRUD operations for templates | ~150 |
| `app/services/template_service.py` | Template business logic service | ~120 |
| `app/models/template.py` | Pydantic request/response schemas | ~100 |
| `app/api/routes_templates.py` | Template CRUD route handlers | ~180 |
| `alembic/versions/xxxx_add_templates.py` | Migration for templates tables | ~60 |
| `tests/test_api_templates.py` | Template CRUD endpoint tests | ~200 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/main.py` | Register template router | ~3 |
| `app/api/deps.py` | Add TemplateServiceDep type alias | ~10 |
| `app/db/session.py` | Import new models for create_tables | ~2 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] POST /v1/templates creates a template with version 1 and returns 201
- [ ] GET /v1/templates returns paginated list excluding soft-deleted templates
- [ ] GET /v1/templates/{id} returns template with active version composition
- [ ] PUT /v1/templates/{id} creates new immutable version and updates active pointer
- [ ] DELETE /v1/templates/{id} soft-deletes without destroying data
- [ ] Composition JSON is validated via Pydantic on create and update
- [ ] Invalid composition returns 422 with clear error details
- [ ] Non-existent template ID returns 404
- [ ] Updating or deleting a soft-deleted template returns appropriate error

### Testing Requirements
- [ ] Unit tests for template CRUD operations
- [ ] Integration tests for all five endpoints
- [ ] Edge case tests (duplicate names, empty compositions, pagination boundaries)

### Non-Functional Requirements
- [ ] Template list endpoint responds in under 200ms at p95 with 100 templates
- [ ] Consistent error response format matching render endpoints

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (ruff clean, type hints on public functions)

---

## 8. Implementation Notes

### Key Considerations
- Template IDs should use the same base-36 generation pattern as render IDs but with a `tmpl_` prefix for clarity
- TemplateVersion IDs use `tver_` prefix
- Variable schema field stores the schema definition but validation is deferred to Session 02
- Composition stored as JSON string in the database (consistent with render input_path pattern but inline for templates since they are small)

### Potential Challenges
- **Atomic version creation + pointer update**: Use a single transaction to create version row and update template.active_version_id
- **Soft-delete with retrievability**: Deleted templates must still be fetchable by direct ID (for historical render references) but excluded from list
- **Composition validation**: Must accept compositions with {{ template variables }} in string fields without failing validation -- defer strict Jinja2 syntax checking to Session 02

### Relevant Considerations
- [P00] **Base-36 render IDs**: Same pattern extended for template/version IDs. Consistent approach across entities.
- [P00] **Import-time DB engine creation**: Avoid this anti-pattern; use lazy initialization as established.

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session:
- Write path (create/update/delete) needs transaction boundaries to prevent partial version+pointer updates
- Query returning unbounded results (list) needs bounded pagination with validated filters and deterministic ordering
- Handler for external input (all endpoints) needs schema-validated input and explicit error mapping

---

## 9. Testing Strategy

### Unit Tests
- Template CRUD functions (create, get, list, update, delete)
- Version creation on update
- Soft-delete behavior

### Integration Tests
- Full endpoint contract tests for all 5 routes
- Pagination behavior (offset, limit, total count)
- Error responses (404, 422, 409)

### Manual Testing
- Create template via curl/httpie
- List, update, and soft-delete via API
- Verify soft-deleted template excluded from list but retrievable by ID

### Edge Cases
- Create template with minimal fields (name + composition only)
- Update template multiple times (version numbers increment correctly)
- Large composition JSON
- Pagination with offset beyond total count
- Concurrent updates to same template

---

## 10. Dependencies

### External Libraries
- SQLModel: 0.0.24
- FastAPI: 0.115.12
- Pydantic: 2.11.2
- Alembic: >=1.15
- aiosqlite: 0.21.0

### Other Sessions
- **Depends on**: phase01-session05-docker-compose-stack (complete)
- **Depended by**: phase02-session02-template-variables-and-rendering

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
