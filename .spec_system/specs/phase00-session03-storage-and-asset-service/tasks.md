# Task Checklist

**Session ID**: `phase00-session03-storage-and-asset-service`
**Total Tasks**: 20
**Estimated Duration**: 2.5-3.5 hours
**Created**: 2026-05-05

---

## Legend

- `[x]` = Completed
- `[ ]` = Pending
- `[P]` = Parallelizable (can run with other [P] tasks)
- `[S0003]` = Session reference (Phase 00, Session 03)
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

- [x] T001 [S0003] Verify prerequisites met -- FFmpeg, ffprobe, Python deps, at least one bundled font available
- [x] T002 [S0003] Create directory structure for deliverables (`app/storage/`, `app/services/`)
- [x] T003 [S0003] Add asset-related settings to config -- MIME allowlist, per-asset download timeout, max image asset size, allow-HTTP toggle, font paths (`app/core/config.py`)

---

## Foundation (5 tasks)

Core structures and base implementations.

- [x] T004 [S0003] Define storage protocol with workspace create, artifact write, artifact read, and artifact list methods (`app/storage/base.py`)
- [x] T005 [S0003] Implement local filesystem storage adapter with deterministic paths from render IDs, with idempotency protection and compensation on failure (`app/storage/local.py`)
- [x] T006 [S0003] Implement SSRF URL and IP validator -- block localhost, loopback, link-local, private networks, metadata endpoints, with schema-validated input and explicit error mapping (`app/services/ssrf.py`)
- [x] T007 [S0003] [P] Implement ffprobe async subprocess wrapper -- extract duration, codec, resolution, stream count, with timeout and failure-path handling (`app/services/ffprobe.py`)
- [x] T008 [S0003] [P] Implement Pillow text-to-image renderer -- font selection, size, color, background, padding, alignment, transparent PNG output (`app/services/text_renderer.py`)

---

## Implementation (8 tasks)

Main feature implementation.

- [x] T009 [S0003] Implement async httpx asset downloader with per-asset timeout, streaming size-limit enforcement (reject before full download), and redirect validation against SSRF (`app/services/asset_service.py`)
- [x] T010 [S0003] Implement MIME type allowlist validation on downloaded assets (`app/services/asset_service.py`)
- [x] T011 [S0003] Implement SHA-256 content-addressed asset cache -- hash after download, store under `data/assets/sha256/ab/cd/<hash>/`, cache-hit bypass, with cleanup on failure (`app/services/asset_service.py`)
- [x] T012 [S0003] Implement ffprobe media validation in asset pipeline -- validate duration, codec, resolution, and stream count against configured limits (`app/services/asset_service.py`)
- [x] T013 [S0003] Implement text asset resolution -- detect TextAsset, render to PNG via text_renderer, return local path (`app/services/asset_service.py`)
- [x] T014 [S0003] Implement top-level `resolve_asset()` entry point that dispatches to download, text render, or file:// resolution based on asset type, with explicit loading, empty, error, and offline states (`app/services/asset_service.py`)
- [x] T015 [S0003] Implement `file://` asset resolution with directory allowlist enforcement from config (`app/services/asset_service.py`)
- [x] T016 [S0003] Add storage and asset service dependency providers to FastAPI deps (`app/api/deps.py`)

---

## Testing (4 tasks)

Verification and quality assurance.

- [x] T017 [S0003] [P] Write SSRF and asset security tests -- blocked IPs (localhost, loopback, link-local, private, metadata), allowed IPs, redirect-to-blocked, size limit, MIME rejection, file:// allowlist (`tests/test_asset_security.py`)
- [x] T018 [S0003] [P] Write storage lifecycle tests -- create workspace, write all 7 artifact types, read back, list, verify deterministic paths (`tests/test_storage.py`)
- [x] T019 [S0003] [P] Write text renderer and ffprobe tests -- PNG output validity, font fallback, empty text, ffprobe mock for duration/codec extraction (`tests/test_text_renderer.py`, `tests/test_ffprobe.py`)
- [x] T020 [S0003] Run full test suite, verify ruff and mypy pass, validate ASCII encoding on all new files

---

## Completion Checklist

Before marking session complete:

- [ ] All tasks marked `[x]`
- [ ] All tests passing
- [ ] All files ASCII-encoded
- [ ] implementation-notes.md updated
- [ ] Ready for the validate workflow step

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
