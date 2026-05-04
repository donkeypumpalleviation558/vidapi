# Implementation Notes

**Session ID**: `phase00-session03-storage-and-asset-service`
**Started**: 2026-05-05 02:32
**Last Updated**: 2026-05-05 02:50

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
- [x] Prerequisites confirmed
- [x] Tools available (FFmpeg 6.1.1, ffprobe, httpx 0.28.1, Pillow 10.2.0)
- [x] Directory structure ready (app/storage/, app/services/ exist)
- [x] Inter font available at /usr/share/fonts/opentype/inter/

---

### Task T001 - Verify prerequisites

**Completed**: 2026-05-05 02:33

**Notes**:
- FFmpeg 6.1.1 and ffprobe available on PATH
- httpx 0.28.1 and Pillow 10.2.0 installed in venv
- Inter font files available at /usr/share/fonts/opentype/inter/

---

### Task T002 - Create directory structure

**Completed**: 2026-05-05 02:33

**Notes**:
- app/storage/ and app/services/ directories already existed from session 01

---

### Task T003 - Add asset-related settings to config

**Completed**: 2026-05-05 02:34

**Notes**:
- Added 5 new settings: asset_download_timeout_seconds, asset_allow_http, asset_mime_allowlist, font_search_paths, ffprobe_timeout_seconds
- MIME allowlist covers image, video, and audio formats needed for MVP

**Files Changed**:
- `app/core/config.py` - Added asset configuration settings

---

### Task T004 - Define storage protocol

**Completed**: 2026-05-05 02:35

**Notes**:
- Protocol pattern with runtime_checkable for future S3 adapter
- ArtifactType StrEnum for all 7 artifact types matching Render model path fields
- Suffix parameter on OUTPUT artifact for format-specific extensions

**Files Changed**:
- `app/storage/base.py` - Created storage protocol and ArtifactType enum

---

### Task T005 - Implement local filesystem storage adapter

**Completed**: 2026-05-05 02:36

**Notes**:
- Deterministic paths: <root>/<render_id>/
- Idempotent workspace creation (exist_ok=True)
- Atomic writes via tmp file + replace for crash safety
- Compensation on failure: removes partial tmp file

**Files Changed**:
- `app/storage/local.py` - Local filesystem storage adapter

---

### Task T006 - Implement SSRF validator

**Completed**: 2026-05-05 02:37

**Notes**:
- Blocks: loopback, private, link-local, reserved, multicast, 0.0.0.0
- Blocks: IPv4-mapped IPv6 addresses (recursive check)
- Blocks: cloud metadata hostnames and paths (GCP, AWS)
- Blocks: credentials in URL netloc
- DNS resolution check: resolves hostname and validates all returned IPs

**Files Changed**:
- `app/services/ssrf.py` - SSRF validation module

---

### Task T007 - Implement ffprobe wrapper

**Completed**: 2026-05-05 02:38

**Notes**:
- Uses asyncio.create_subprocess_exec (non-blocking)
- Configurable timeout with proper process cleanup on timeout
- Parses JSON output for duration, codecs, resolution, stream count
- Handles missing fields and non-numeric durations gracefully

**Files Changed**:
- `app/services/ffprobe.py` - Async ffprobe subprocess wrapper

---

### Task T008 - Implement text-to-image renderer

**Completed**: 2026-05-05 02:39

**Notes**:
- Renders text to RGBA PNG with transparent or colored background
- Supports font family resolution via search paths
- Font cache for performance
- Handles empty text (1x1 transparent PNG), multiline, padding, alignment

**Files Changed**:
- `app/services/text_renderer.py` - Pillow text-to-image renderer

---

### Tasks T009-T015 - Asset service implementation

**Completed**: 2026-05-05 02:42

**Notes**:
- T009: Async httpx downloader with manual redirect following for SSRF validation per hop
- T010: MIME allowlist validation from response Content-Type header
- T011: SHA-256 content-addressed cache under data/assets/sha256/ab/cd/<hash>/
- T012: ffprobe integration via safe_probe that returns None for non-media files
- T013: Text asset renders to PNG via text_renderer, stored in workspace or cache
- T014: Top-level resolve_asset() dispatches by scheme: http(s), file://, or TextAsset
- T015: file:// resolution with directory allowlist enforcement from config

**Files Changed**:
- `app/services/asset_service.py` - Complete asset resolution service

---

### Task T016 - Add dependency providers

**Completed**: 2026-05-05 02:43

**Notes**:
- LocalStorage and AssetService providers with lru_cache(maxsize=1)
- Type aliases: StorageDep, AssetServiceDep

**Files Changed**:
- `app/api/deps.py` - Added storage and asset service dependency injection

---

### Task T017 - SSRF and asset security tests

**Completed**: 2026-05-05 02:44

**Notes**:
- 32 tests covering SSRF, MIME, size limits, file:// allowlist
- Parametrized over all blocked IP ranges

**Files Changed**:
- `tests/test_asset_security.py` - Security-focused test suite

---

### Task T018 - Storage lifecycle tests

**Completed**: 2026-05-05 02:45

**Notes**:
- 15 tests covering workspace lifecycle, all 7 artifact types, deterministic paths
- Uses tmp_path fixture for isolation

**Files Changed**:
- `tests/test_storage.py` - Storage adapter test suite

---

### Task T019 - Text renderer and ffprobe tests

**Completed**: 2026-05-05 02:46

**Notes**:
- 9 text renderer tests: PNG validity, transparency, colored background, empty text, multiline, padding, font fallback, alignment
- 8 ffprobe tests: JSON parsing, async probe with mocked subprocess, error handling

**Files Changed**:
- `tests/test_text_renderer.py` - Text renderer test suite
- `tests/test_ffprobe.py` - ffprobe wrapper test suite

---

### Task T020 - Final validation

**Completed**: 2026-05-05 02:50

**Notes**:
- 163/163 tests passing (0.49s)
- ruff check: all checks passed
- ruff format: all files formatted
- mypy: no issues found in 10 source files
- ASCII encoding: all 10 new files clean

---

## Design Decisions

### Decision 1: Manual redirect following for SSRF

**Context**: httpx supports automatic redirect following, but we need to validate each redirect target against SSRF rules.
**Chosen**: Manual redirect loop with per-hop SSRF validation
**Rationale**: Prevents redirect-to-private-IP attacks that bypass initial URL validation

### Decision 2: Atomic writes for storage and cache

**Context**: Partial writes from crashes could leave corrupted artifacts
**Chosen**: Write to .tmp file then atomic replace
**Rationale**: Ensures either full artifact or no artifact; compensates by cleaning up tmp on failure

### Decision 3: Font resolution via search paths

**Context**: Font locations vary across OS and container environments
**Chosen**: Configurable search paths with recursive file search and family-to-filename mapping
**Rationale**: Works across dev machines and Docker containers without hardcoded paths

---
