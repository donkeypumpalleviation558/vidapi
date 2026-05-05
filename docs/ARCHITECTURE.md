# Architecture

## System Overview

VidAPI is a self-hosted FastAPI service that accepts JSON timeline compositions
and renders video through pluggable renderer backends. The MVP uses Editly
(a Node.js tool backed by FFmpeg) as the default renderer, invoked as a
subprocess from an async Python pipeline.

## Dependency Graph

```
Client
  |
  | POST /v1/renders (JSON composition)
  v
FastAPI API (validate, create record, run pipeline)
  |
  v
Render Service
  |-- Merge Service (variable substitution)
  |-- Asset Service (fetch, validate, cache)
  |   |-- SSRF Validator
  |   |-- ffprobe (media validation)
  |   |-- Text Renderer (Pillow PNG)
  |
  |-- Renderer (compile + render)
  |   |-- Editly Renderer (Node subprocess)
  |   |   |-- Segment Compiler (timeline -> sequential clips)
  |   |   |-- FFmpeg (invoked by Editly)
  |   |
  |   |-- Poster Generator (FFmpeg frame extraction)
  |
  |-- Storage Adapter (persist artifacts)
  v
SQLite Database (render metadata)
Local Filesystem (render artifacts)
```

## Components

### FastAPI API
- **Purpose**: HTTP layer -- validates requests, delegates to services, returns responses
- **Tech**: FastAPI, Pydantic v2, structlog
- **Location**: `app/api/`

### Composition Models
- **Purpose**: Pydantic v2 schemas for the public JSON composition format
- **Tech**: Pydantic v2 discriminated unions for asset types
- **Location**: `app/models/composition.py`

### Render Service
- **Purpose**: Orchestrates the full render pipeline (validate, resolve, compile, render, store)
- **Tech**: Python async, structlog context binding
- **Location**: `app/services/render_service.py`

### Asset Service
- **Purpose**: Resolves remote/local/text assets with SSRF protection, MIME validation, and caching
- **Tech**: httpx (async), Pillow (text rendering), ffprobe (media validation)
- **Location**: `app/services/asset_service.py`

### Editly Renderer
- **Purpose**: Compiles VidAPI compositions to Editly JSON and invokes Editly as a Node subprocess
- **Tech**: Segment compiler (pure functions), asyncio subprocess
- **Location**: `app/renderers/editly.py`

### Segment Compiler
- **Purpose**: Converts absolute-time timeline clips into sequential Editly clips with layers
- **Tech**: Pure functions -- collect boundaries, generate segments, map layers
- **Location**: `app/renderers/editly.py` (functions: `collect_boundaries`, `generate_segments`)

### Poster Generator
- **Purpose**: Extracts a frame from rendered video as a JPEG poster
- **Tech**: FFmpeg subprocess
- **Location**: `app/renderers/poster.py`

### Storage Adapter
- **Purpose**: Persists render artifacts to a deterministic directory structure
- **Tech**: Protocol-based (local filesystem for dev, S3-compatible planned for production)
- **Location**: `app/storage/`

### Database
- **Purpose**: Render job metadata persistence
- **Tech**: SQLModel + aiosqlite (dev), Alembic migrations
- **Location**: `app/db/`

## Tech Stack Rationale

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| FastAPI | Web framework | Async-native, Pydantic integration, auto OpenAPI docs |
| Pydantic v2 | Schema validation | Discriminated unions for asset types, fast validation |
| SQLModel + aiosqlite | Database | Async SQLite for dev, same API for future PostgreSQL |
| Alembic | Migrations | Standard Python migration tool, async-compatible |
| structlog | Logging | Structured JSON logs with context binding |
| httpx | HTTP client | Async, manual redirect control for SSRF validation |
| Pillow | Text rendering | Deterministic text-to-PNG with bundled fonts |
| Editly (Node.js) | Video rendering | Declarative timeline editing, reduces custom FFmpeg work |
| FFmpeg | Video encoding | Industry standard, poster extraction, media probing |
| hatchling | Build backend | Modern, lightweight, explicit package discovery |

## Data Layer

- **Database**: SQLite (development), PostgreSQL planned for production
- **Migration Tool**: Alembic, migrations in `alembic/versions/`, sequential numbering
- **Storage**: Local filesystem under `data/renders/<render_id>/`

## Data Flow

1. Client POSTs JSON composition to `/v1/renders`
2. Pydantic validates the composition schema
3. Render record created in SQLite with status `queued`
4. Merge variables substituted if present
5. Assets resolved: remote fetched via httpx, text rendered to PNG, all cached by SHA-256
6. Segment compiler converts absolute-time timeline to sequential Editly clips
7. Compiled Editly JSON + replay metadata written to workspace
8. Editly invoked as Node subprocess with timeout
9. Poster extracted from output via FFmpeg
10. Artifacts persisted to storage: input.json, expanded.json, compiled.editly.json, replay.json, output.mp4, poster.jpg, logs.txt
11. Render status updated to `succeeded` or `failed`
12. Client polls GET `/v1/renders/{id}` for status and download URL

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Editly over raw FFmpeg | Editly subprocess | Reduces custom filter graph code for MVP |
| Segment compiler as pure functions | No class state | Easier to test, clearer data flow |
| Base-36 render IDs | No ULID dependency | Minimal dependencies for MVP; proper ULID in Phase 03 |
| Non-fatal poster generation | Warning on failure | Missing poster should not fail a successful render |
| Manual redirect following | Per-hop SSRF check | Prevents redirect-to-private-IP attacks |
| Track 0 on bottom | Natural z-order | Matches Editly layer ordering |

See [.spec_system/PRD/PRD.md](.spec_system/PRD/PRD.md) for full architecture decisions.
