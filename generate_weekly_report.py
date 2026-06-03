from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import Integer, func

from database import ApiCheck, SessionLocal


def pct(value: float) -> str:
    return f"{value:.1f}%"


def ms(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.0f}ms"


def query_window(db, start: datetime, end: datetime):
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


# def pick_best_provider(current):
#     if not current:
#         return None

#     candidates = []
#     for provider, s in current.items():
#         latency = s["avg_latency"] if s["avg_latency"] is not None else 10**9
#         candidates.append((provider, s["uptime"], latency))

#     candidates.sort(key=lambda x: (-x[1], x[2]))
#     return candidates[0][0]


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

        # Weighted score favors uptime regressions first.
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


def build_report() -> str:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        start = now - timedelta(days=7)

        prev_end = start
        prev_start = prev_end - timedelta(days=7)

        current = query_window(db, start, now)
        previous = query_window(db, prev_start, prev_end)

        rows = []
        for provider in sorted(current.keys()):
            s = current[provider]
            rows.append(
                {
                    "provider": provider,
                    "total": s["total"],
                    "successful": s["successful"],
                    "uptime": s["uptime"],
                    "avg_latency": s["avg_latency"],
                    "min_latency": s["min_latency"],
                    "max_latency": s["max_latency"],
                }
            )

        total_checks = sum(r["total"] for r in rows) if rows else 0
        total_success = sum(r["successful"] or 0 for r in rows) if rows else 0
        overall_uptime = (total_success / total_checks * 100) if total_checks else 0.0

        # best_provider = pick_best_provider(current)
        biggest_regression = pick_biggest_regression(current, previous)
        recommendation = make_operational_recommendation(best_provider, biggest_regression)

        lines = []
        lines.append("# AI API Weekly Reliability Report")
        lines.append("")
        lines.append(f"Generated (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Window (UTC): {start.strftime('%Y-%m-%d %H:%M:%S')} -> {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- Best provider this week: {best_provider or 'N/A'}")
        lines.append(f"- Biggest regression: {biggest_regression or 'No material regression detected'}")
        lines.append(f"- Operational recommendation: {recommendation}")
        lines.append("")
        lines.append("## Overview")
        lines.append("")
        lines.append(f"- Total checks: {total_checks}")
        lines.append(f"- Successful checks: {total_success}")
        lines.append(f"- Overall uptime: {pct(overall_uptime)}")
        lines.append("")
        lines.append("## Provider Breakdown")
        lines.append("")

        if not rows:
            lines.append("No data available for the last 7 days.")
        else:
            lines.append("| Provider | Checks | Success | Uptime | Avg Latency | Min | Max |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|")
            for r in rows:
                lines.append(
                    f"| {r['provider']} | {r['total']} | {r['successful']} | {pct(r['uptime'])} | {ms(r['avg_latency'])} | {ms(r['min_latency'])} | {ms(r['max_latency'])} |"
                )

        lines.append("")
        lines.append("## Notes")
        lines.append("")
        lines.append("- Latency values are based on successful checks in the selected window.")
        lines.append("- Failed checks are included in uptime calculations.")

        return "\n".join(lines)
    finally:
        db.close()


def main() -> None:
    report = build_report()
    output_dir = Path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "latest-weekly-report.md"
    output_file.write_text(report, encoding="utf-8")

    print(f"Weekly report generated at: {output_file}")


if __name__ == "__main__":
    main()
