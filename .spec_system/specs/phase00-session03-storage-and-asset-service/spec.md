# Session Specification

**Session ID**: `phase00-session03-storage-and-asset-service`
**Phase**: 00 - Foundation
**Status**: Not Started
**Created**: 2026-05-05

---

## 1. Session Overview

This session implements the local filesystem storage adapter and the secure asset resolution service -- the two infrastructure layers that the Editly renderer (Session 04) and the render service (Session 05) depend on. Storage handles deterministic workspace creation and artifact persistence for render jobs. The asset service handles downloading remote media, validating URLs against SSRF attacks, enforcing size and MIME limits, caching assets by content hash, running ffprobe for media validation, and rendering text assets to transparent PNG images with Pillow.

These components sit between the composition schema (Session 02) and the renderer (Session 04). Without them, the renderer has no way to resolve remote media URLs into local files, and completed renders have no durable artifact storage. Both the synchronous render path (Phase 00) and the async worker path (Phase 01) will call the same storage and asset service interfaces, so getting the abstractions right here matters.

The session also delivers the first security-focused tests in the project: SSRF protection, redirect validation, size-limit enforcement, and MIME allowlisting. These are MVP requirements, not hardening tasks, per the PRD.

---

## 2. Objectives

1. Implement a storage protocol and local filesystem adapter that creates deterministic render workspaces and persists all 7 artifact types
2. Implement a secure asset resolution service that fetches remote media with SSRF protection, size limits, MIME validation, timeout, and redirect checks
3. Implement SHA-256 content-addressed asset caching to avoid redundant downloads
4. Implement an ffprobe wrapper for media validation (duration, codec, stream count)
5. Implement text-to-image rendering with Pillow and bundled font paths for deterministic text overlays

---

## 3. Prerequisites

### Required Sessions
- [x] `phase00-session01-project-skeleton-and-config` - FastAPI skeleton, config system, structured logging
- [x] `phase00-session02-composition-schema-and-db-models` - Pydantic composition models, Render DB model

### Required Tools/Knowledge
- Python 3.11+ with httpx, Pillow, structlog
- FFmpeg 6+ and ffprobe available on PATH
- Understanding of SSRF attack vectors and IP network classification

### Environment Requirements
- Local development environment with FFmpeg and ffprobe installed
- At least one bundled font (Inter, Roboto, or Noto Sans) accessible by path

---

## 4. Scope

### In Scope (MVP)
- Storage protocol (abstract base) defining the artifact persistence interface
- Local filesystem storage adapter with deterministic paths from render IDs
- Render workspace lifecycle: create, write artifacts, read artifacts, list artifacts
- SSRF validator: block localhost, loopback, link-local, private IPs, metadata endpoints
- Redirect validation: reject redirects to blocked networks
- Remote asset download via httpx with per-asset timeout and max size enforcement
- MIME type allowlist enforcement before accepting downloaded assets
- SHA-256 content-addressed asset cache under `data/assets/sha256/`
- ffprobe wrapper: extract duration, codec, resolution, and stream count from media files
- Text-to-image rendering with Pillow: font, size, color, background, padding, alignment
- Asset security tests covering all blocked URL patterns
- Storage integration tests for workspace lifecycle

### Out of Scope (Deferred)
- S3-compatible storage adapter - *Reason: Phase 03 Production Hardening*
- HTML asset rendering - *Reason: Phase 04 HyperFrames renderer*
- Advanced audio processing - *Reason: Phase 01 multi-track*
- Asset resolution during API request path - *Reason: always in worker/render service*

---

## 5. Technical Approach

### Architecture

The storage layer uses a protocol/interface pattern so that local filesystem storage and future S3 storage share the same contract. The asset service composes SSRF validation, httpx download, MIME checks, size enforcement, content hashing, and ffprobe into a single `resolve_asset()` entry point.

```
Asset Service
  |-- SSRF Validator (IP/network checks)
  |-- httpx client (async download)
  |-- MIME validator
  |-- SHA-256 hasher + cache lookup
  |-- ffprobe wrapper (media metadata)
  |-- Text renderer (Pillow)

Storage Protocol
  |-- Local Filesystem Adapter
  |-- (S3 Adapter - Phase 03)
```

### Design Patterns
- Protocol/ABC: Storage protocol decouples interface from implementation
- Content-addressing: SHA-256 dedup avoids re-downloading identical assets
- Composition: Asset service composes validators and downloaders rather than inheriting

### Technology Stack
- httpx 0.28 for async HTTP downloads
- Pillow 11.2 for text-to-image rendering
- asyncio.create_subprocess_exec for ffprobe invocation
- pathlib.Path for all filesystem operations
- structlog for operation logging

---

## 6. Deliverables

### Files to Create
| File | Purpose | Est. Lines |
|------|---------|------------|
| `app/storage/__init__.py` | Package init | ~1 |
| `app/storage/base.py` | Storage protocol definition | ~60 |
| `app/storage/local.py` | Local filesystem storage adapter | ~150 |
| `app/services/__init__.py` | Package init | ~1 |
| `app/services/asset_service.py` | Asset resolution, download, validation, caching | ~250 |
| `app/services/ssrf.py` | SSRF URL and IP validation | ~100 |
| `app/services/ffprobe.py` | ffprobe subprocess wrapper | ~80 |
| `app/services/text_renderer.py` | Pillow text-to-image rendering | ~120 |
| `tests/test_storage.py` | Storage adapter tests | ~120 |
| `tests/test_asset_security.py` | SSRF and asset validation tests | ~180 |
| `tests/test_ffprobe.py` | ffprobe wrapper tests | ~60 |
| `tests/test_text_renderer.py` | Text rendering tests | ~80 |

### Files to Modify
| File | Changes | Est. Lines |
|------|---------|------------|
| `app/core/config.py` | Add asset-related settings (MIME allowlist, timeout, HTTP toggle) | ~15 |
| `app/api/deps.py` | Add storage and asset service dependency providers | ~15 |

---

## 7. Success Criteria

### Functional Requirements
- [ ] Local storage creates deterministic workspace paths from render IDs
- [ ] All 7 render artifact types can be written and read from local storage
- [ ] Remote HTTPS assets download successfully with proper validation
- [ ] Localhost, private IPs, link-local, and metadata endpoints are blocked
- [ ] Redirects to blocked networks are caught and rejected
- [ ] Assets exceeding size limits are rejected before full download
- [ ] Invalid MIME types are rejected
- [ ] SHA-256 cache avoids redundant downloads for identical assets
- [ ] Text renders to transparent PNG with specified font, size, color, and padding
- [ ] ffprobe extracts duration, codec, resolution, and stream info from media files

### Testing Requirements
- [ ] Storage lifecycle tests (create workspace, write, read, list)
- [ ] SSRF tests cover all blocked IP ranges and redirect scenarios
- [ ] Asset size and MIME validation tests
- [ ] Text renderer produces valid PNG images
- [ ] ffprobe tests with mock or fixture media

### Non-Functional Requirements
- [ ] All asset downloads use async I/O (httpx, not requests)
- [ ] ffprobe invoked via asyncio subprocess (not blocking subprocess.run)

### Quality Gates
- [ ] All files ASCII-encoded
- [ ] Unix LF line endings
- [ ] Code follows project conventions (ruff, mypy clean)

---

## 8. Implementation Notes

### Key Considerations
- The `Settings` class already defines `storage_root`, `render_workspace_root`, `asset_cache_root`, and `allowed_asset_dirs` -- use these directly
- The Render DB model already has path fields (`input_path`, `output_path`, etc.) -- storage adapter should return paths compatible with these
- httpx is already a project dependency; Pillow is already a dependency
- Config already has `max_asset_size_mb` -- asset service should read from Settings

### Potential Challenges
- SSRF validation must handle IPv4-mapped IPv6 addresses and DNS rebinding: use resolved IP checks after DNS lookup
- ffprobe may not be installed in all dev environments: tests should skip gracefully or use mocks
- Font paths vary across OS/container: text renderer should accept explicit font paths from config

### Relevant Considerations
- **FFmpeg subprocess spawning needs resource limits**: Apply to ffprobe as well (timeout, memory)
- **Remote asset fetching needs timeouts and size limits**: Enforced in asset service from day one
- **Avoid synchronous rendering in API process**: All I/O through async httpx and async subprocess

### Behavioral Quality Focus
Checklist active: Yes
Top behavioral risks for this session's deliverables:
- Asset download with timeout, retry/backoff, and failure-path handling
- SSRF validator with schema-validated input and explicit error mapping
- Storage write path with idempotency protection and compensation on failure
- ffprobe call with timeout, failure-path handling

---

## 9. Testing Strategy

### Unit Tests
- SSRF validator: test each blocked IP range, allowed IPs, edge cases (IPv4-mapped IPv6, DNS to private IP)
- MIME validator: test allowed and disallowed content types
- SHA-256 cache: test cache hit and cache miss paths
- Text renderer: test PNG output dimensions, transparency, font selection

### Integration Tests
- Storage lifecycle: create workspace, write all artifact types, read back, verify paths
- Asset download: mock httpx responses for success, size limit, timeout, redirect

### Manual Testing
- Download a real HTTPS image and verify it caches correctly
- Render a text string to PNG and visually inspect the output

### Edge Cases
- Asset URL with credentials in netloc
- Redirect chain ending at a blocked IP
- Zero-byte download response
- ffprobe on a corrupted or non-media file
- Text rendering with empty string
- Workspace creation when parent directory does not exist

---

## 10. Dependencies

### External Libraries
- httpx: 0.28.1 (already installed)
- Pillow: 11.2.1 (already installed)
- structlog: 25.1.0 (already installed)

### Other Sessions
- **Depends on**: phase00-session01 (config, logging), phase00-session02 (composition models, render DB model)
- **Depended by**: phase00-session04 (renderer needs resolved assets and storage), phase00-session05 (render service needs storage and assets)

---

## Next Steps

Run the implement workflow step to begin AI-led implementation.
