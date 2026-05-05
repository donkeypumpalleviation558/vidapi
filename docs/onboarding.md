# Onboarding

## Prerequisites

- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed (for Editly renderer)
- [ ] FFmpeg 6+ and ffprobe installed
- [ ] uv package manager installed (recommended) or pip
- [ ] Git configured

## Setup Steps

1. Clone: `git clone <repo-url> && cd vidapi`
2. Create venv: `uv venv .venv && source .venv/bin/activate`
3. Install: `uv pip install -e ".[dev]"`
4. Start: `uvicorn app.main:app --reload`

## Required Fonts

The text renderer requires at least one of these font families:

- Inter (preferred) -- `fonts-inter` on Debian/Ubuntu
- Roboto -- `fonts-roboto` on Debian/Ubuntu
- Noto Sans -- `fonts-noto` on Debian/Ubuntu
- DejaVu Sans -- `fonts-dejavu-core` on Debian/Ubuntu

## Verify Setup

- [ ] API runs at `http://localhost:8000`
- [ ] Health check passes: `curl http://localhost:8000/v1/health`
- [ ] Tests pass: `pytest`
- [ ] Lint passes: `ruff check .`
- [ ] Types pass: `mypy app/`

## Docker Alternative

```bash
docker compose up --build
curl http://localhost:8000/v1/health
```

## Key Files to Read First

| File | Purpose |
|------|---------|
| `.spec_system/PRD/PRD.md` | Full product requirements |
| `.spec_system/CONVENTIONS.md` | Coding standards |
| `docs/ARCHITECTURE.md` | System design and data flow |
| `app/models/composition.py` | Public JSON schema |
| `app/renderers/editly.py` | Segment compiler and Editly bridge |
| `app/services/render_service.py` | Render pipeline orchestration |
