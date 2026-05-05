# Development Guide

## Required Tools

- Python 3.11+ (tested with 3.12.3)
- Node.js 20+ (tested with v24.14.0)
- FFmpeg 6+ and ffprobe (tested with 6.1.1)
- uv (recommended package manager)

## Port Mappings

| Service | Port | URL |
|---------|------|-----|
| FastAPI API | 8000 | http://localhost:8000 |
| OpenAPI docs | 8000 | http://localhost:8000/docs |
| ReDoc | 8000 | http://localhost:8000/redoc |

## Dev Scripts

| Command | Purpose |
|---------|---------|
| `uvicorn app.main:app --reload` | Start dev server with auto-reload |
| `ruff check .` | Run linter |
| `ruff format .` | Format code |
| `ruff check --fix .` | Auto-fix lint issues |
| `mypy app/` | Type check application code |
| `pytest` | Run full test suite |
| `pytest -x` | Stop on first failure |
| `pytest -k test_name` | Run specific test |
| `alembic upgrade head` | Apply database migrations |
| `alembic downgrade base` | Reset database |

## Database

1. Start: Database auto-creates on first API startup (`data/vidapi.db`)
2. Migrate: `alembic upgrade head`
3. Reset: `alembic downgrade base && alembic upgrade head`

SQLite is used for development. PostgreSQL support is planned for Phase 03.

## Testing

```bash
pytest                    # Run all tests (226+)
pytest -v                 # Verbose output
pytest --tb=short         # Short tracebacks
pytest tests/test_segment_compiler.py  # Run specific test file
```

Tests use in-memory SQLite and mock renderers. No external services needed.

## Quality Gates

Run all quality gates before committing:

```bash
ruff check . && ruff format --check . && mypy app/ && pytest
```

## Pre-commit Hooks

Pre-commit is configured in `.pre-commit-config.yaml`. Install hooks:

```bash
pre-commit install
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/vidapi.db` | Database connection string |
| `STORAGE_ROOT` | `./data` | Root directory for render artifacts |
| `DEBUG` | `false` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `EDITLY_BIN` | `editly` | Path to Editly binary |
| `EDITLY_TIMEOUT_SECONDS` | `600` | Editly subprocess timeout |
| `ASSET_DOWNLOAD_TIMEOUT_SECONDS` | `60` | Remote asset download timeout |
| `ASSET_ALLOW_HTTP` | `false` | Allow HTTP (non-HTTPS) asset URLs |
