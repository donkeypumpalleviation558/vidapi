# Deployment

## Local Dev (Sync Mode)

```bash
uvicorn app.main:app --reload    # Start server (RENDER_MODE=sync, no Redis needed)
curl localhost:8000/v1/health    # Verify
# Ctrl+C to stop
```

## Docker Compose (Async Mode)

```bash
docker compose up --build        # Build and start API + worker + Redis
curl localhost:8000/v1/health    # Verify (should show redis: ok)
bash scripts/smoke-test.sh       # End-to-end render test
docker compose down              # Stop
```

Three services run on a shared bridge network:

| Service | Image | Purpose |
|---------|-------|---------|
| `api` | `Dockerfile.api` | FastAPI + Uvicorn (Python-only, slim) |
| `worker` | `Dockerfile.worker` | ARQ consumer + Node.js + Editly + FFmpeg + Xvfb |
| `redis` | `redis:7-alpine` | ARQ job queue broker |

### Image Details

- **Dockerfile.api**: Slim Python image with curl for health checks, non-root `vidapi` user
- **Dockerfile.worker**: Multi-stage build (node:20-slim for Editly, python:3.11-slim runtime), includes GL libraries and Xvfb for headless rendering, non-root `vidapi` user

Environment defaults live in `.env.docker`.

## Local Dev (Async Mode, No Docker)

```bash
redis-server &                                   # Start Redis
RENDER_MODE=async uvicorn app.main:app --reload  # Start API in async mode
arq app.workers.arq_settings.WorkerSettings      # Start worker (separate terminal)
```

## CI/CD Pipeline

```
Push --> Lint/Format/Type Check --> Test (336+ tests) --> Build Docker Image
```

GitHub Actions workflows at `.github/workflows/`.

## Render Artifact Storage

Each render produces artifacts in a deterministic directory:

```
data/renders/<render_id>/
  input.json              # Original composition
  expanded.json           # After merge variable substitution
  compiled.editly.json    # Compiled Editly spec
  replay.json             # Subprocess command and environment for replay
  output.mp4              # Rendered video
  poster.jpg              # Poster frame
  logs.txt                # Structured render log (stage entries)
```

## Health Check

- **Endpoint**: `GET /v1/health`
- **Response**: `{"status": "ok", "service": "VidAPI", "redis": {"status": "ok"}}`
- **Redis check**: Skipped in sync mode, PING with 2s timeout in async mode
- **API probe**: Every 30s, 5s timeout, 3 retries
- **Worker probe**: Redis key-based health check via `scripts/worker-healthcheck.sh`

## Rollback

Docker rollback:

```bash
docker compose down
docker compose up -d --no-build   # Restart previous image
```

**When to rollback**: Health check fails post-deploy, error rate spikes, or
renderer subprocess failures increase.

## Production Deployment (Planned)

Phase 03 will add:
- PostgreSQL for metadata
- S3-compatible storage for artifacts
- API key authentication
- Rate limiting
