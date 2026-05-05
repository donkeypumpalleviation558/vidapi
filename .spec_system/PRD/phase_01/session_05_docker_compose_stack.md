# Session 05: Docker Compose Stack

**Session ID**: `phase01-session05-docker-compose-stack`
**Status**: Not Started
**Estimated Tasks**: ~18
**Estimated Duration**: 2-3 hours

---

## Objective

Deliver a Docker Compose stack that runs the API, worker, and Redis as independent services with shared configuration, health checks, and verified end-to-end render flow from container startup.

---

## Scope

### In Scope (MVP)
- Dockerfile for API service (FastAPI + Uvicorn)
- Dockerfile for worker service (Python + Node + Editly + FFmpeg + fonts)
- Docker Compose configuration with API, worker, and Redis services
- Shared volume for local storage in development
- Environment variable configuration for Redis URL and shared settings
- Health checks for API, worker, and Redis
- .dockerignore optimization (already started in Phase 00)
- Non-root user in containers
- Bundled fonts (Inter, Roboto, Noto Sans) in worker image
- End-to-end smoke test: submit render via API, worker processes, poll until done
- Documentation for running the stack

### Out of Scope
- PostgreSQL container (Phase 03)
- MinIO/S3 container (Phase 03)
- Production hardening and secrets management (Phase 03)
- CI/CD pipeline (Phase transition)
- Multi-stage build optimization (future)

---

## Prerequisites

- [ ] Sessions 01-04 complete (async worker with full pipeline)
- [ ] Docker and Docker Compose available in development environment

---

## Deliverables

1. Dockerfile.api for the API service
2. Dockerfile.worker for the worker service
3. docker-compose.yml with API, worker, and Redis
4. Health check configuration for all services
5. End-to-end smoke test script or instructions
6. Updated development documentation

---

## Success Criteria

- [ ] `docker compose up` starts API, worker, and Redis successfully
- [ ] API responds to GET /v1/health from host machine
- [ ] POST /v1/renders returns 202 and worker picks up job
- [ ] Worker completes render and status transitions to succeeded
- [ ] Containers run as non-root user
- [ ] All services have working health checks
- [ ] Worker image includes FFmpeg, Node.js, Editly, and bundled fonts
