# Environments

| Environment | URL | Purpose |
|-------------|-----|---------|
| Development | http://localhost:8000 | Local development |
| Docker Dev | http://localhost:8000 | Docker Compose local stack |
| Staging | TBD (Phase 03) | Pre-production testing |
| Production | TBD (Phase 03) | Live system |

## Configuration Differences

| Config | Dev (local) | Dev (Docker) | Production (planned) |
|--------|-------------|--------------|----------------------|
| Database | SQLite file | SQLite file | PostgreSQL |
| Storage | Local filesystem | Local filesystem (volume) | S3-compatible |
| Debug mode | true | true | false |
| Log format | Console | Console | JSON |
| Asset HTTP | Allowed | Allowed | HTTPS only |
| Auth | None | None | API key required |

## Required Environment Variables

- `DATABASE_URL`: Database connection string (SQLite for dev, PostgreSQL for prod)
- `STORAGE_ROOT`: Root directory for render artifacts and asset cache
- `DEBUG`: Enable debug mode and console log output
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

See [development.md](development.md) for the full environment variable reference.
