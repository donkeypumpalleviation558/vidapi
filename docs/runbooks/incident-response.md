# Incident Response

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | API completely down | Immediate |
| P1 | All renders failing | < 1 hour |
| P2 | Specific render types failing | < 4 hours |
| P3 | Minor feature broken, cosmetic | Next business day |

## Common Incidents

### API Not Responding
**Symptoms**: Health check returns non-200 or times out
**Resolution**:
1. Check container status: `docker compose ps`
2. Check logs: `docker compose logs api`
3. Restart: `docker compose restart api`
4. If persistent, rebuild: `docker compose up --build`

### Renders Failing with Editly Timeout
**Symptoms**: Renders stuck in `rendering` status, eventually fail with timeout error
**Resolution**:
1. Check render logs at `data/renders/<render_id>/logs.txt`
2. Check system resources (CPU, memory, disk)
3. Review the compiled spec at `data/renders/<render_id>/compiled.editly.json`
4. Replay the render manually using `data/renders/<render_id>/replay.json`
5. If asset-related, check asset cache under `data/assets/`

### Renders Failing with Missing Editly Binary
**Symptoms**: Renders fail immediately with `FileNotFoundError` for editly
**Resolution**:
1. Verify Node.js is installed: `node --version`
2. Verify Editly is installed: `which editly` or `npx editly --help`
3. Check `EDITLY_BIN` environment variable

### Database Migration Errors
**Symptoms**: API fails to start, migration-related errors in logs
**Resolution**:
1. Check current migration state: `alembic current`
2. Apply pending migrations: `alembic upgrade head`
3. If corrupted, reset (dev only): `alembic downgrade base && alembic upgrade head`
