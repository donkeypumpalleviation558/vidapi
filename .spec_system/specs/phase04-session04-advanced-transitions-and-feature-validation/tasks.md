# Task Checklist

**Session ID**: `phase04-session04-advanced-transitions-and-feature-validation`
**Total Tasks**: 21
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
| Testing | 5 | 5 | 0 |
| **Total** | **21** | **21** | **0** |

---

## Setup (3 tasks)

Initial configuration and environment preparation.

- [x] T001 [S0404] Verify current transition schema, capability, limit, and Editly compiler behavior before changing transition handling (`app/renderers/editly.py`)
- [x] T002 [S0404] [P] Create transition documentation scaffold for supported values, placement rules, timing constraints, and examples (`docs/transitions.md`)
- [x] T003 [S0404] [P] Confirm no migration or seed update is required because transition data remains stored inside composition JSON (`tests/test_alembic_migrations.py`)

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T004 [S0404] Add advanced transition enum values, public aliases, and placement rules with schema-validated input and explicit error mapping (`app/models/composition.py`)
- [x] T005 [S0404] [P] Create public-to-Editly transition mapping helpers with an explicit allowlist and deterministic canonical names (`app/renderers/transitions.py`)
- [x] T006 [S0404] Add pure transition boundary validation for same-track successors, gaps, overlaps, duration bounds, and same-boundary conflicts (`app/renderers/transitions.py`)
- [x] T007 [S0404] Expand renderer capability declarations and unsupported transition issue context without exposing raw payload or asset data (`app/renderers/capabilities.py`)
- [x] T008 [S0404] Update shared model exports for the expanded transition enum contract and import compatibility (`app/models/__init__.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T009 [S0404] Wire transition semantic validation into shared composition limit validation so API, template, and worker paths fail before renderer invocation (`app/services/limits.py`)
- [x] T010 [S0404] Replace hard-coded Editly fade mapping with shared transition mapper while preserving existing fade and crossfade output (`app/renderers/editly.py`)
- [x] T011 [S0404] Update Editly transition boundary selection to use validated plans with state reset on re-entry and no cached transition state (`app/renderers/editly.py`)
- [x] T012 [S0404] Ensure renderer capability validation rejects unsupported transition combinations at the closest boundary with bounded deterministic context (`app/renderers/capabilities.py`)
- [x] T013 [S0404] Update render API documentation with a compact advanced transition request example and validation behavior (`README.md`)
- [x] T014 [S0404] Update architecture documentation for transition validation, capability checks, and compiler mapping flow (`docs/ARCHITECTURE.md`)
- [x] T015 [S0404] Update renderer capability matrix and extension notes for the advanced transition allowlist (`docs/renderer-capabilities.md`)
- [x] T016 [S0404] Complete transition behavior documentation with supported values, fallback semantics, invalid timing examples, and renderer notes (`docs/transitions.md`)

---

## Testing (5 tasks)

Verification and quality assurance.

- [x] T017 [S0404] [P] Write transition schema and semantic validation tests for aliases, placement, gaps, overlaps, duration bounds, and boundary conflicts (`tests/test_transitions.py`)
- [x] T018 [S0404] [P] Write renderer capability tests for supported advanced transitions, unavailable renderers, and redacted unsupported-feature context (`tests/test_renderer_capabilities.py`)
- [x] T019 [S0404] [P] Write Editly compiler tests for deterministic advanced transition mapping and existing fade/crossfade backward compatibility (`tests/test_editly_compiler.py`)
- [x] T020 [S0404] Update API render tests for valid advanced transitions and invalid timing failures with schema-validated input and explicit error mapping (`tests/test_api_renders.py`)
- [x] T021 [S0404] Run targeted tests, ruff, mypy where feasible, and ASCII validation on all session artifacts (`tests/test_transitions.py`)

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
