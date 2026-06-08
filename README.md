# OpsLedger

OpsLedger is a small Flask operations dashboard for facility teams. It tracks maintenance work orders, shows summary metrics, and exposes a few HTML and JSON endpoints used by dispatchers.

The project is intentionally compact but split across service, route, template, and test layers so evaluation tasks can exercise multi-file reasoning.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest
flask --app opsledger.app run
```

## Current Features

- Work order list with status and priority filters.
- Dashboard summary for open, blocked, and completed work.
- Work order detail page with activity notes.
- JSON API for work order search.

