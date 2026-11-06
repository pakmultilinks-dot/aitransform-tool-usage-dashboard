"""Generate mock aiTransform tool usage data (MOCK DATA, not real users).

35 days: 2026-10-03 to 2026-11-06. Fixed seed 42, so the output is reproducible.
Each row: date, hour (0-23 PKT), tool, file_type, sessions.

Method (documented in METHOD.md):
- Base level: about 85 sessions per day on average.
- Day factor: weekdays 1.15, weekends 0.65 (weekends quieter).
- Trend: linear rise from 0.90 to 1.10 across the 35 days (slight upward trend).
- Hour weights: peak 10:00-13:00 and 19:00-22:00 PKT, very quiet 02:00-06:00.
- Tool weights: AI Writer 0.30, AI Image Generator 0.22, AI Code Generator 0.15,
  AI Chatbot 0.14, Speech to Text 0.10, AI VoiceOver 0.09.
- Sessions per (day, hour, tool) cell: a Poisson sample of the expected value
  (Knuth's method for small means, normal approximation above 30).
  Cells with 0 sessions are not written out.
- File type per row: weighted random choice from the tool's file types.

Writes data/usage.csv and data/usage.json (same rows), and prints the insight
numbers used in INSIGHTS.md.
"""

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
START = date(2026, 10, 3)
DAYS = 35
BASE_DAILY = 85.0

TOOLS = {
    "AI Writer": (0.30, {"txt": 0.55, "docx": 0.30, "pdf": 0.15}),
    "AI Image Generator": (0.22, {"png": 0.60, "jpg": 0.40}),
    "AI Code Generator": (0.15, {"py": 0.40, "js": 0.35, "html": 0.25}),
    "AI Chatbot": (0.14, {"txt": 1.00}),
    "Speech to Text": (0.10, {"mp3": 0.55, "wav": 0.45}),
    "AI VoiceOver": (0.09, {"mp3": 0.60, "wav": 0.40}),
}

# Hour weights for 0..23 (PKT). Peaks 10-13 and 19-22, quiet 02-06.
# Normalised below so they sum to 1.0.
HOUR_WEIGHTS = [
    0.008, 0.005, 0.003, 0.002, 0.002, 0.004,  # 00-05
    0.012, 0.025, 0.045, 0.065, 0.085, 0.090,  # 06-11
    0.085, 0.080, 0.060, 0.050, 0.045, 0.040,  # 12-17
    0.035, 0.075, 0.085, 0.075, 0.040, 0.020,  # 18-23
]
_total_hw = sum(HOUR_WEIGHTS)
HOUR_WEIGHTS = [w / _total_hw for w in HOUR_WEIGHTS]
assert abs(sum(HOUR_WEIGHTS) - 1.0) < 0.001, sum(HOUR_WEIGHTS)


def pick_weighted(rng, weights):
    roll = rng.random()
    total = 0.0
    for key, weight in weights.items():
        total += weight
        if roll <= total:
            return key
    return list(weights)[-1]


def poisson(rng, lam):
    """Poisson sample (Knuth's method for small lambda, normal approx above 30)."""
    if lam <= 0:
        return 0
    if lam < 30:
        limit = math.exp(-lam)
        k = 0
        p = 1.0
        while True:
            p *= rng.random()
            if p <= limit:
                return k
            k += 1
    return max(0, round(rng.gauss(lam, math.sqrt(lam))))


def main():
    rng = random.Random(SEED)
    rows = []
    for day_index in range(DAYS):
        day = START + timedelta(days=day_index)
        weekday = day.weekday() < 5
        day_factor = 1.15 if weekday else 0.65
        trend = 0.90 + 0.20 * (day_index / (DAYS - 1))
        for hour in range(24):
            for tool, (tool_weight, file_types) in TOOLS.items():
                expected = BASE_DAILY * day_factor * trend * HOUR_WEIGHTS[hour] * tool_weight
                sessions = poisson(rng, expected)
                if sessions == 0:
                    continue
                rows.append({
                    "date": day.isoformat(),
                    "hour": hour,
                    "tool": tool,
                    "file_type": pick_weighted(rng, file_types),
                    "sessions": sessions,
                })

    rows.sort(key=lambda r: (r["date"], r["hour"], r["tool"]))
    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(exist_ok=True)

    with open(out_dir / "usage.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "hour", "tool", "file_type", "sessions"])
        writer.writeheader()
        writer.writerows(rows)

    with open(out_dir / "usage.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    # Insight numbers, computed from the generated rows (used in INSIGHTS.md).
    total = sum(r["sessions"] for r in rows)
    by_tool = {}
    by_hour = {}
    by_date = {}
    weekday_total, weekday_days, weekend_total, weekend_days = 0, 0, 0, 0
    seen_dates = {}
    for r in rows:
        by_tool[r["tool"]] = by_tool.get(r["tool"], 0) + r["sessions"]
        by_hour[r["hour"]] = by_hour.get(r["hour"], 0) + r["sessions"]
        by_date[r["date"]] = by_date.get(r["date"], 0) + r["sessions"]
    for day_index in range(DAYS):
        day = START + timedelta(days=day_index)
        daily = by_date.get(day.isoformat(), 0)
        if day.weekday() < 5:
            weekday_total += daily
            weekday_days += 1
        else:
            weekend_total += daily
            weekend_days += 1
    top_tool, top_count = max(by_tool.items(), key=lambda kv: kv[1])
    peak_hour, peak_count = max(by_hour.items(), key=lambda kv: kv[1])
    first_week = sum(by_date.get((START + timedelta(days=i)).isoformat(), 0) for i in range(7)) / 7
    last_week = sum(by_date.get((START + timedelta(days=i)).isoformat(), 0) for i in range(28, 35)) / 7
    print("rows:", len(rows))
    print("total sessions:", total)
    print("date range:", rows[0]["date"], "to", rows[-1]["date"])
    print("by tool:", dict(sorted(by_tool.items(), key=lambda kv: -kv[1])))
    print("most used tool:", top_tool, top_count)
    print("peak hour:", peak_hour, "with", peak_count, "sessions")
    print("weekday avg sessions per day:", round(weekday_total / weekday_days, 1),
          "over", weekday_days, "weekdays")
    print("weekend avg sessions per day:", round(weekend_total / weekend_days, 1),
          "over", weekend_days, "weekend days")
    print("first week daily avg:", round(first_week, 1))
    print("last week daily avg:", round(last_week, 1))
    print("trend change first to last week:", round((last_week - first_week) / first_week * 100, 1), "%")


if __name__ == "__main__":
    main()
