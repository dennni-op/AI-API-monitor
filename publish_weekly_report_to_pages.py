from datetime import datetime, timedelta
from html import escape
from pathlib import Path

from sqlalchemy import Integer, func

from database import ApiCheck, SessionLocal


def query_stats(db, start: datetime, end: datetime):
    rows = (
        db.query(
            ApiCheck.provider,
            func.count(ApiCheck.id).label("total"),
            func.sum(func.cast(ApiCheck.success, Integer)).label("successful"),
            func.avg(ApiCheck.latency_ms).label("avg_latency"),
            func.min(ApiCheck.latency_ms).label("min_latency"),
            func.max(ApiCheck.latency_ms).label("max_latency"),
        )
        .filter(ApiCheck.timestamp >= start, ApiCheck.timestamp < end)
        .group_by(ApiCheck.provider)
        .order_by(ApiCheck.provider)
        .all()
    )

    data = {}
    for r in rows:
        total = int(r.total or 0)
        successful = int(r.successful or 0)
        uptime = (successful / total * 100.0) if total else 0.0
        data[r.provider] = {
            "total": total,
            "successful": successful,
            "uptime": uptime,
            "avg_latency": float(r.avg_latency) if r.avg_latency is not None else None,
            "min_latency": float(r.min_latency) if r.min_latency is not None else None,
            "max_latency": float(r.max_latency) if r.max_latency is not None else None,
        }
    return data


def fmt_ms(value):
    if value is None:
        return "N/A"
    return f"{value:.0f}ms"


def fmt_pct(value):
    return f"{value:.1f}%"


def trend_symbol(current, previous, lower_is_better=False):
    if current is None or previous is None:
        return "-"

    if abs(current - previous) < 0.01:
        return "flat"

    if lower_is_better:
        return "better" if current < previous else "worse"
    return "better" if current > previous else "worse"


def pick_best_provider(current):
    candidates = []
    for provider, s in current.items():
        # Prefer high uptime first, then low average latency.
        latency = s["avg_latency"] if s["avg_latency"] is not None else 10**9
        candidates.append((provider, s["uptime"], latency))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (-x[1], x[2]))
    return candidates[0][0]


def pick_biggest_regression(current, previous):
    worst_provider = None
    worst_score = 0.0
    reasons = []

    for provider, s in current.items():
        p = previous.get(provider)
        if not p:
            continue

        uptime_drop = max(0.0, p["uptime"] - s["uptime"])
        lat_now = s["avg_latency"]
        lat_prev = p["avg_latency"]
        latency_increase = 0.0
        if lat_now is not None and lat_prev is not None:
            latency_increase = max(0.0, lat_now - lat_prev)

        score = (uptime_drop * 100.0) + latency_increase
        if score > worst_score:
            worst_score = score
            worst_provider = provider
            reasons = []
            if uptime_drop > 0:
                reasons.append(f"uptime down {uptime_drop:.1f}pp")
            if latency_increase > 0:
                reasons.append(f"latency up {latency_increase:.0f}ms")

    if not worst_provider:
        return None

    reason_text = ", ".join(reasons) if reasons else "mixed performance decline"
    return f"{worst_provider} ({reason_text})"


def make_operational_recommendation(best_provider, biggest_regression):
    if not best_provider and not biggest_regression:
        return "Collect another full week of data before making routing changes."

    if best_provider and biggest_regression:
        reg_provider = biggest_regression.split(" ")[0]
        return (
            f"Keep primary traffic on {best_provider}; set alerts and fallback routing for {reg_provider} "
            "until next week's trend confirms recovery."
        )

    if best_provider:
        return f"Use {best_provider} as the default choice this week and monitor for sudden regressions."

    return "Keep current routing but increase alert sensitivity for providers showing weaker trends."


def load_manual_notes():
    notes_path = Path("reports/manual-notes-latest.md")
    if not notes_path.exists():
        return ""
    return notes_path.read_text(encoding="utf-8").strip()


def build_report_html(now, start, end, current, previous, manual_notes):
    total_checks = sum(s["total"] for s in current.values())
    total_success = sum(s["successful"] for s in current.values())
    overall_uptime = (total_success / total_checks * 100.0) if total_checks else 0.0
    best = pick_best_provider(current)
    biggest_regression = pick_biggest_regression(current, previous)
    recommendation = make_operational_recommendation(best, biggest_regression)

    rows_html = []
    providers = sorted(current.keys())
    for provider in providers:
        c = current[provider]
        p = previous.get(provider, {})

        uptime_trend = trend_symbol(c["uptime"], p.get("uptime"), lower_is_better=False)
        latency_trend = trend_symbol(c["avg_latency"], p.get("avg_latency"), lower_is_better=True)

        rows_html.append(
            "<tr>"
            f"<td>{escape(provider)}</td>"
            f"<td>{c['total']}</td>"
            f"<td>{c['successful']}</td>"
            f"<td>{fmt_pct(c['uptime'])}</td>"
            f"<td>{fmt_ms(c['avg_latency'])}</td>"
            f"<td>{fmt_ms(c['min_latency'])}</td>"
            f"<td>{fmt_ms(c['max_latency'])}</td>"
            f"<td>{uptime_trend}</td>"
            f"<td>{latency_trend}</td>"
            "</tr>"
        )

    notes_html = ""
    if manual_notes:
        notes_html = (
            "<section><h2>Analyst Notes (Manual)</h2>"
            f"<pre>{escape(manual_notes)}</pre></section>"
        )

    best_text = best if best else "N/A"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>AI API Weekly Report - {now.strftime('%Y-%m-%d')}</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem auto; max-width: 980px; padding: 0 1rem; line-height: 1.5; }}
    h1, h2 {{ margin-bottom: 0.4rem; }}
    .meta {{ color: #555; margin-bottom: 1rem; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin: 1rem 0 1.25rem; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 0.8rem; }}
    .label {{ font-size: 0.85rem; color: #666; }}
    .value {{ font-size: 1.1rem; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.45rem; text-align: left; font-size: 0.95rem; }}
    th {{ background: #f6f6f6; }}
    pre {{ background: #fafafa; border: 1px solid #eee; padding: 0.8rem; border-radius: 8px; white-space: pre-wrap; }}
    .small {{ color: #666; font-size: 0.9rem; }}
    a {{ color: #0a66c2; text-decoration: none; }}
  </style>
</head>
<body>
  <p><a href=\"../index.html\">Back to report archive</a></p>
  <h1>AI API Weekly Reliability Report</h1>
  <p class=\"meta\">Generated (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
  <p class=\"small\">Window: {start.strftime('%Y-%m-%d %H:%M:%S')} to {end.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>

  <div class=\"cards\">
    <div class=\"card\"><div class=\"label\">Total checks</div><div class=\"value\">{total_checks}</div></div>
    <div class=\"card\"><div class=\"label\">Successful checks</div><div class=\"value\">{total_success}</div></div>
    <div class=\"card\"><div class=\"label\">Overall uptime</div><div class=\"value\">{fmt_pct(overall_uptime)}</div></div>
    <div class=\"card\"><div class=\"label\">Best provider (week)</div><div class=\"value\">{escape(best_text)}</div></div>
  </div>

    <section>
        <h2>Executive Summary</h2>
        <ul>
            <li><strong>Best provider this week:</strong> {escape(best if best else 'N/A')}</li>
            <li><strong>Biggest regression:</strong> {escape(biggest_regression if biggest_regression else 'No material regression detected')}</li>
            <li><strong>Operational recommendation:</strong> {escape(recommendation)}</li>
        </ul>
    </section>

  <section>
    <h2>Provider Breakdown</h2>
    <table>
      <thead>
        <tr>
          <th>Provider</th>
          <th>Checks</th>
          <th>Success</th>
          <th>Uptime</th>
          <th>Avg Latency</th>
          <th>Min</th>
          <th>Max</th>
          <th>Uptime Trend</th>
          <th>Latency Trend</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows_html) if rows_html else '<tr><td colspan="9">No data for this week.</td></tr>'}
      </tbody>
    </table>
    <p class=\"small\">Trend compares this week vs previous 7-day window. Uptime: higher is better. Latency: lower is better.</p>
  </section>

  {notes_html}
</body>
</html>
"""


def update_index(report_entries):
    docs = Path("docs")
    docs.mkdir(parents=True, exist_ok=True)
    index = docs / "index.html"

    rows = []
    for date_str, filename in report_entries:
        rows.append(f"<li><a href=\"reports/{filename}\">Weekly Report - {date_str}</a></li>")

    latest_link_html = ""
    if report_entries:
        latest_link_html = '<p><a href="reports/latest.html">Open latest report</a></p>'

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>AI API Reliability Reports</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem auto; max-width: 900px; padding: 0 1rem; line-height: 1.5; }}
    li {{ margin: 0.4rem 0; }}
    a {{ color: #0a66c2; text-decoration: none; }}
    .small {{ color: #666; }}
  </style>
</head>
<body>
  <h1>AI API Reliability Reports</h1>
  <p class=\"small\">Public weekly reliability archive generated from monitoring data.</p>
    {latest_link_html}
  <h2>Archive</h2>
  <ul>
    {''.join(rows) if rows else '<li>No reports yet.</li>'}
  </ul>
</body>
</html>
"""
    index.write_text(html, encoding="utf-8")


def write_latest_permalink(latest_filename: str):
        latest_file = Path("docs/reports/latest.html")
        html = f"""<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <meta http-equiv=\"refresh\" content=\"0; url=./{latest_filename}\">
    <title>Latest Weekly Report</title>
</head>
<body>
    <p>Redirecting to latest report: <a href=\"./{latest_filename}\">{latest_filename}</a></p>
</body>
</html>
"""
        latest_file.write_text(html, encoding="utf-8")


def main():
    now = datetime.utcnow()
    end = now
    start = end - timedelta(days=7)
    prev_end = start
    prev_start = prev_end - timedelta(days=7)

    db = SessionLocal()
    try:
        current = query_stats(db, start, end)
        previous = query_stats(db, prev_start, prev_end)
    finally:
        db.close()

    manual_notes = load_manual_notes()
    html = build_report_html(now, start, end, current, previous, manual_notes)

    reports_dir = Path("docs/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    date_str = now.strftime("%Y-%m-%d")
    filename = f"weekly-report-{date_str}.html"
    out_file = reports_dir / filename
    out_file.write_text(html, encoding="utf-8")

    entries = []
    for p in sorted(reports_dir.glob("weekly-report-*.html"), reverse=True):
        d = p.stem.replace("weekly-report-", "")
        entries.append((d, p.name))

    if entries:
        write_latest_permalink(entries[0][1])

    update_index(entries)

    print(f"Published report page: {out_file}")


if __name__ == "__main__":
    main()
