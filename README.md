# AI-API-monitor

Monitor OpenAI, Anthropic, and Google API health/latency on a schedule and save results to a database.

## What This Repo Does

- Runs periodic checks for:
	- OpenAI (`gpt-4.1-mini`)
	- Anthropic (`claude-opus-4-6`)
	- Google (`gemini-2.5-flash`)
- Saves each check to `api_checks` table via SQLAlchemy.
- Can run locally or via GitHub Actions cron.


### 1) Add GitHub Repository Secrets

In GitHub, go to `Settings -> Secrets and variables -> Actions -> New repository secret`.

Add:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `DATABASE_URL`

`DATABASE_URL` examples:

- Neon/Supabase Postgres:
	- `postgresql://user:password@host:5432/dbname?sslmode=require`
- Local SQLite fallback (not recommended for Actions persistence):
	- Leave empty and SQLite will be used in the runner only.

### 2) Enable the Workflow

The workflow is in [.github/workflows/monitor.yml](.github/workflows/monitor.yml).

It runs:

- Every hour (`0 * * * *`)
- Manually via `workflow_dispatch`

### 3) Run Once Manually

In GitHub:

- Go to `Actions -> AI API Monitor -> Run workflow`
- Confirm it succeeds

If successful, rows should be inserted into your `api_checks` table.

## Local Run

### Install

```bash
pip install -r requirements.txt
```

### Set environment variables

Create a `.env` file (local only):

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
DATABASE_URL=postgresql://...
```

### Run monitor once

```bash
python monitor_and_save.py
```

### Optional: Run local scheduler loop

```bash
python scheduler.py
```

## Key Files

- [monitor_and_save.py](monitor_and_save.py): one-off run that checks providers and writes to DB
- [scheduler.py](scheduler.py): local continuous scheduler
- [database.py](database.py): SQLAlchemy models/connection
- [.github/workflows/monitor.yml](.github/workflows/monitor.yml): GitHub Actions hourly schedule

## Notes

- GitHub Actions cron can be delayed by a few minutes under load.
- Free-tier databases have limits; monitor usage and retention.
- If you hit SSL issues with Postgres, verify your `DATABASE_URL` includes `sslmode=require`.

## Automated Weekly Reports

A second workflow generates a weekly Markdown report from your database.

- Workflow: [.github/workflows/weekly-report.yml](.github/workflows/weekly-report.yml)
- Script: [generate_weekly_report.py](generate_weekly_report.py)
- Output file: [reports/latest-weekly-report.md](reports/latest-weekly-report.md)

It runs:

- Every Monday at 08:00 UTC
- Manually via `workflow_dispatch`

### Run the report now

In GitHub:

- Go to `Actions -> Weekly Reliability Report -> Run workflow`

After completion:

- Read the report in the run summary
- Or download the `weekly-reliability-report` artifact

## Publish Reports to GitHub Pages

You can publish a public report archive without building a separate website.

### How this works

- Metrics and tables are automated from your database.
- Analyst commentary is manual via [reports/manual-notes-latest.md](reports/manual-notes-latest.md).
- The weekly workflow builds an HTML report and commits it to `docs/`.
- GitHub Pages serves the `docs/` folder as your public site.

Files involved:

- [publish_weekly_report_to_pages.py](publish_weekly_report_to_pages.py)
- [docs/index.html](docs/index.html) (generated)
- [docs/reports/](docs/reports/) (generated archive)

### One-time GitHub Pages setup

1. Go to `Settings -> Pages` in your repository.
2. Under `Build and deployment`, choose:
	- `Source`: `Deploy from a branch`
	- `Branch`: `main`
	- `Folder`: `/docs`
3. Save.

### Weekly process (hybrid)

1. Update [reports/manual-notes-latest.md](reports/manual-notes-latest.md) with your analysis (best model, trends, recommendations).
2. Run `Weekly Reliability Report` workflow manually (or wait for schedule).
3. The workflow will:
	- Generate report metrics
	- Generate a public HTML page under `docs/reports/`
	- Update `docs/index.html` archive
	- Commit and push changes

Your public archive URL will be:

- `https://<your-github-username>.github.io/<your-repo-name>/`