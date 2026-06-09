# AGENTS.md

## Cursor Cloud specific instructions

### Repository branch

`main` currently contains only a minimal README. The full Job Radar application lives on branch `cursor/build-job-radar-app-8f64`. Check out that branch before installing dependencies or running the app:

```bash
git fetch origin cursor/build-job-radar-app-8f64
git checkout cursor/build-job-radar-app-8f64
```

### Stack overview

Single Python monolith (FastAPI + Uvicorn). No Node.js, Docker, or separate database server. SQLite is embedded at `database/job_radar.db` and is created automatically on startup.

### System dependency

Ubuntu/Debian images need `python3.12-venv` before `python -m venv .venv` works:

```bash
sudo apt-get install -y python3.12-venv
```

### Run the dev server

From repo root with the virtualenv activated:

```bash
source .venv/bin/activate
JOB_RADAR_SCRAPE_ON_STARTUP=false uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Set `JOB_RADAR_SCRAPE_ON_STARTUP=false` for faster startup when you only need the UI. Live scraping uses Playwright Chromium and can take several minutes (or hang) against France Travail / Indeed from cloud VMs.

See [README.md](README.md) for environment variables and generic scraper configuration.

### Lint / tests

There is no configured linter or test suite in this repository. Basic sanity checks:

```bash
source .venv/bin/activate
python3 -m compileall -q app database models routes scrapers
python3 -c "from app.main import app"
```

### Hello-world verification

1. Open http://127.0.0.1:8000 — dashboard with stats for the active user.
2. Visit `/jobs`, `/saved`, and `/settings`.
3. POST to `/settings` or use the settings form to update user preferences.
4. POST to `/jobs/{id}/status` with `status=saved` to exercise the saved-jobs pipeline.
