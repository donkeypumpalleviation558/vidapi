# Deployment

## Local Dev

```bash
uvicorn app.main:app --reload    # Start server
curl localhost:8000/v1/health    # Verify
# Ctrl+C to stop
```

## Docker Dev

```bash
docker compose up --build        # Build and start
curl localhost:8000/v1/health    # Verify
docker compose down              # Stop
```

The Docker image is a multi-stage build:
1. **node-base**: Installs Editly globally via npm
2. **runtime**: Python 3.11 + Node.js binary + FFmpeg + bundled fonts

Container runs as non-root `vidapi` user with health checks configured.

## CI/CD Pipeline

```
Push --> Lint/Format/Type Check --> Test (226+ tests) --> Build Docker Image
```

GitHub Actions quality workflow is configured at `.github/workflows/quality.yml`.

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
  logs.txt                # Renderer stderr output
```

## Health Check

- **Endpoint**: `GET /v1/health`
- **Response**: `{"status": "ok", "service": "VidAPI", "version": "0.1.5"}`
- **Docker probe**: Every 30s, 5s timeout, 3 retries

## Rollback

Docker rollback:

```bash
docker compose down
docker compose up -d --no-build   # Restart previous image
```

**When to rollback**: Health check fails post-deploy, error rate spikes, or
renderer subprocess failures increase.

## Production Deployment (Planned)

Phase 01+ will add:
- Redis + ARQ worker queue (async rendering)
- PostgreSQL for metadata
- S3-compatible storage for artifacts
- API key authentication
- Rate limiting
