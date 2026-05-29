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