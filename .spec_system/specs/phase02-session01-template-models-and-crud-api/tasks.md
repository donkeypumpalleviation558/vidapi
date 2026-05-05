# Task Checklist

**Session ID**: `phase02-session01-template-models-and-crud-api`
**Total Tasks**: 20
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
| Implementation | 8 | 8 | 0 |
| Testing | 4 | 4 | 0 |
| **Total** | **20** | **20** | **0** |

---

## Setup (3 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0201] Verify prerequisites met: Phase 01 complete, SQLModel operational, async DB sessions working (`app/db/session.py`)
- [x] T002 [S0201] Create Alembic migration for templates and template_versions tables with all columns, constraints, and indexes (`alembic/versions/`)
- [x] T003 [S0201] Register new template models in DB session create_tables to ensure table creation in dev mode (`app/db/session.py`)

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T004 [S0201] [P] Create Template SQLModel with id, name, description, active_version_id, variable_schema JSON, is_deleted flag, created_at, updated_at (`app/db/template_models.py`)
- [x] T005 [S0201] [P] Create TemplateVersion SQLModel with id, template_id, version_number, composition JSON, variable_schema JSON, created_at (`app/db/template_models.py`)
- [x] T006 [S0201] [P] Create Pydantic request models: CreateTemplateRequest, UpdateTemplateRequest with composition validation (`app/models/template.py`)
- [x] T007 [S0201] [P] Create Pydantic response models: TemplateResponse, TemplateListItem, TemplateListResponse with pagination metadata (`app/models/template.py`)
- [x] T008 [S0201] Create ID generation helpers for template (tmpl_ prefix) and version (tver_ prefix) entities following established base-36 pattern (`app/db/template_models.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T009 [S0201] Implement template_crud.create_template with atomic version-1 creation and active_version_id pointer assignment, with transaction boundaries (`app/db/template_crud.py`)
- [x] T010 [S0201] Implement template_crud.get_template_by_id returning template with active version data, with explicit error mapping for not-found (`app/db/template_crud.py`)
- [x] T011 [S0201] Implement template_crud.list_templates with bounded pagination, validated filters, deterministic ordering by created_at DESC, and soft-delete exclusion (`app/db/template_crud.py`)
- [x] T012 [S0201] Implement template_crud.update_template creating new immutable version row and updating active pointer atomically, with idempotency protection and transaction boundaries (`app/db/template_crud.py`)
- [x] T013 [S0201] Implement template_crud.soft_delete_template setting is_deleted flag with state reset prevention on already-deleted templates (`app/db/template_crud.py`)
- [x] T014 [S0201] Create template service layer wrapping CRUD with business validation (composition parse check, soft-delete guard on update/delete) (`app/services/template_service.py`)
- [x] T015 [S0201] Implement routes_templates.py with all five CRUD endpoints, schema-validated input, and explicit error mapping for 404/409/422 (`app/api/routes_templates.py`)
- [x] T016 [S0201] Wire template router into main app and add TemplateServiceDep to deps.py (`app/main.py`, `app/api/deps.py`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T017 [S0201] [P] Write unit tests for template CRUD functions: create, get, list, update, soft-delete (`tests/test_template_crud.py`)
- [x] T018 [S0201] [P] Write integration tests for all five template endpoints: success paths, 404, 422, pagination (`tests/test_api_templates.py`)
- [x] T019 [S0201] Write edge case tests: version increment on multiple updates, soft-deleted excluded from list but retrievable by ID, pagination beyond total (`tests/test_api_templates.py`)
- [x] T020 [S0201] Run full test suite, validate ASCII encoding on all new files, verify ruff clean (`tests/`)

---

## Completion Checklist

Before marking session complete:

- [x] All tasks marked `[x]`
- [x] All tests passing
- [x] All files ASCII-encoded
- [x] implementation-notes.md updated
- [x] Ready for the validate workflow step
