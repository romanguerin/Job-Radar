# Job Radar

Job Radar is a small FastAPI web application that collects job offers from multiple sources and displays deterministic match scores for two predefined users.

It is designed for personal use on a laptop, home server, or small VPS.

## Features

- Two predefined users with editable preferences stored in SQLite
- Playwright-based scrapers for:
  - France Travail
  - Indeed
  - Configurable generic job boards
- Automatic background collection every 30 minutes
- Location-aware collection using each user's preferred locations
- Duplicate removal using a stable job fingerprint
- Deterministic scoring without AI:
  - base relevance: 20
  - +20 category match
  - +20 location match
  - +20 salary above minimum
  - +20 preferred keyword found
  - -20 excluded keyword found
  - capped between 0 and 100
- Dark Bootstrap dashboard with:
  - total jobs found
  - jobs added today
  - top matching jobs
  - recent jobs
- Job list filters for category, location, source, and minimum score
- Sorting by highest score, newest, or salary
- Job detail page with Save Job, Mark Applied, and Mark Rejected actions
- Saved jobs page split by saved, applied, and rejected statuses

## Project structure

```text
app/          FastAPI app entry point, scoring, services, scheduler
database/     SQLite session and database initialization
models/       SQLAlchemy database models
routes/       Dashboard, jobs, saved jobs, and settings routes
scrapers/     France Travail, Indeed, and generic scraper modules
static/       CSS and JavaScript
templates/    Jinja2 HTML templates
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Run the app

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

On startup, the application automatically:

1. Creates the SQLite database at `database/job_radar.db`
2. Creates the database tables
3. Creates two predefined users
4. Starts the 30-minute background scheduler
5. Runs an initial scraping job unless disabled

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `JOB_RADAR_DATABASE_URL` | `sqlite:///database/job_radar.db` | SQLAlchemy database URL |
| `JOB_RADAR_SCHEDULER_MINUTES` | `30` | Scraping interval in minutes |
| `JOB_RADAR_SCRAPE_ON_STARTUP` | `true` | Run a collection job at startup |
| `JOB_RADAR_GENERIC_SOURCES` | `[]` | JSON configuration for generic scraper sources |

If you want to start quickly without scraping on startup:

```bash
JOB_RADAR_SCRAPE_ON_STARTUP=false uvicorn app.main:app --reload
```

## Generic scraper configuration

The generic scraper reads `JOB_RADAR_GENERIC_SOURCES` as JSON. Each source can define selectors for job cards and fields.

For local sites that expose search URLs, use URL placeholders:

- `{term}` URL-encoded preferred category or keyword
- `{location}` URL-encoded preferred location
- `{raw_term}` unencoded preferred category or keyword
- `{raw_location}` unencoded preferred location

Example:

```bash
export JOB_RADAR_GENERIC_SOURCES='[
  {
    "name": "Example Jobs",
    "url": "https://example.com/jobs?q={term}&city={location}",
    "category": "software",
    "limit": 20,
    "selectors": {
      "card": ".job-card",
      "title": ".job-title",
      "company": ".company",
      "location": ".location",
      "salary": ".salary",
      "contract": ".contract",
      "description": ".summary",
      "link": "a"
    }
  }
]'
```

Then start the app normally:

```bash
uvicorn app.main:app --reload
```

## Add a new job source

1. Create a new module in `scrapers/`.
2. Implement `JobScraper` from `scrapers/base.py`.
3. Return normalized `ScrapedJob` objects.
4. Add the scraper class to `scrapers/registry.py`.

The collector will automatically deduplicate saved jobs and calculate scores for both users.
