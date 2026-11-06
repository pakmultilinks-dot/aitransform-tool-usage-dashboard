# aiTransform Tool Usage Dashboard (Mock Data)

A simple dashboard that shows how users might use aiTransform's tools, built
on mock data. It answers three questions: how much usage happens per day,
which tools get used most, and when peak hours fall.

All data is mock data, generated with a fixed seed. It is not real user data.
The page says so at the top, and the insights in INSIGHTS.md carry the same
warning.

## What it shows
- KPI cards: total sessions in the selected range, most used tool, peak hour,
  and average sessions per day.
- Daily usage: a line chart of sessions per day.
- Most used tools: a bar chart of sessions per tool.
- Peak hours: a bar chart of sessions per hour of day (PKT).
- A date filter (start and end date) that re-filters the charts and the KPIs.

## Files
- `index.html`: the dashboard (loads Chart.js from a CDN, reads `data/usage.json`).
- `generate_data.py`: the mock data generator (seed 42, reproducible).
- `data/usage.csv` and `data/usage.json`: the generated data, 35 days
  (3 October to 6 November 2026), 1,875 rows, 3,038 sessions.
- `METHOD.md`: exactly how the mock data was made (seed, weights, assumptions).
- `INSIGHTS.md`: a half-page summary of what the mock data shows.
- `.env.example`: placeholder settings only, no secrets.

## Setup
Run it locally from the project folder:

```
python3 generate_data.py   # regenerate data/usage.csv and data/usage.json
python3 -m http.server 8000
```

Then open http://localhost:8000 in a browser. The dashboard must be served
over HTTP; opening index.html directly from disk does not work, because
browsers block the fetch of `data/usage.json` from file URLs.

To deploy: push this folder to a GitHub repository and turn on GitHub Pages
for the main branch. No build step and no server code are needed.

## How it was tested
1. Ran `generate_data.py` fresh and confirmed the CSV and JSON hold the same
   1,875 rows and the same 3,038 total sessions.
2. Served the folder with `python3 -m http.server` and confirmed index.html
   returns HTTP 200 and references `data/usage.json`.
3. Confirmed the HTML contains the three charts (daily line, tools bar, hours
   bar) and the start and end date filter inputs.
4. Checked the insight numbers in INSIGHTS.md against the generator output
   (totals, tool shares, peak hours, weekday vs weekend averages, first-week
   vs last-week trend).

## Limitations
- The data is mock data, not real aiTransform usage. No business decision
  should rest on it.
- Chart.js loads from a CDN, so the charts need internet access. The data
  itself is local.
- The date filter runs in the browser only; there is no backend and no saved
  state.
- The dashboard shows totals only. It has no per-user, per-account, or
  revenue view, because the mock dataset does not contain that information.
