# VidAPI

Self-hosted Python FastAPI service for programmatic video rendering.
Accepts JSON timeline compositions and renders video via Editly + FFmpeg.
A self-hosted, open-source alternative to Creatomate and JSON2Video.

## Quick Start

```bash
# One command (Docker)
docker compose up --build

# Or local development
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn app.main:app --reload

# Verify
curl http://localhost:8000/v1/health
```

## Prerequisites

- Python 3.11+
- Node.js 20+ (for Editly renderer)
- FFmpeg 6+ and ffprobe
- Bundled fonts: Inter, Roboto, or Noto Sans

## Repository Structure

```
.
|-- app/
|   |-- api/               # Route handlers, dependencies, error handling
|   |-- core/              # Config (pydantic-settings), logging, security
|   |-- db/                # SQLModel tables, CRUD, async sessions
|   |-- models/            # Pydantic composition and render schemas
|   |-- renderers/         # Renderer protocol, Editly bridge, poster gen
|   |-- services/          # Render pipeline, asset service, SSRF, merge
|   |-- storage/           # Storage protocol and local filesystem adapter
|   \-- workers/           # Background job workers (Phase 01)
|-- alembic/               # Database migrations
|-- tests/                 # 226+ tests (schema, security, compiler, API)
|-- docs/                  # Architecture, development, deployment guides
|-- Dockerfile             # Multi-stage: Node + Python + FFmpeg + fonts
|-- docker-compose.yml     # One-command local stack
\-- pyproject.toml         # Dependencies and tool config
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/health` | Health check |
| `POST` | `/v1/renders` | Create a render job |
| `GET` | `/v1/renders/{id}` | Get render status |
| `GET` | `/v1/renders/{id}/download` | Download rendered output |

Interactive API docs at `http://localhost:8000/docs` (Swagger) or `/redoc`.

## Documentation

- [Getting Started](docs/onboarding.md)
- [Development Guide](docs/development.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](docs/deployment.md)
- [Environments](docs/environments.md)
- [Contributing](CONTRIBUTING.md)

## Tech Stack

- **FastAPI** - Async web framework with auto OpenAPI docs
- **Pydantic v2** - Discriminated unions for composition schema validation
- **SQLModel + aiosqlite** - Async database (SQLite dev, PostgreSQL planned)
- **Alembic** - Database migrations
- **Editly** - Default video renderer (Node.js subprocess)
- **FFmpeg** - Video encoding, poster extraction, media probing
- **Pillow** - Text-to-image rendering with bundled fonts
- **httpx** - Async asset downloads with SSRF protection
- **structlog** - Structured JSON logging

## Project Status

Phase 00 (Foundation) is complete. See [PRD](.spec_system/PRD/PRD.md) for
current progress and roadmap.

| Phase | Name | Status |
|-------|------|--------|
| 00 | Foundation | Complete (5/5 sessions) |
| 01 | Async Jobs and Multi-track | In Progress (1/5 sessions) |
| 02 | Templates and Polish | Not Started |
| 03 | Production Hardening | Not Started |
| 04 | Advanced Rendering | Not Started |

## License

[MIT](LICENSE)
