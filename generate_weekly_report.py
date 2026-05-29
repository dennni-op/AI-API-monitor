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


def build_report() -> str:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        start = now - timedelta(days=7)

        rows = (
            db.query(
                ApiCheck.provider,
                func.count(ApiCheck.id).label("total"),
                func.sum(func.cast(ApiCheck.success, Integer)).label("successful"),
                func.avg(ApiCheck.latency_ms).label("avg_latency"),
                func.min(ApiCheck.latency_ms).label("min_latency"),
                func.max(ApiCheck.latency_ms).label("max_latency"),
            )
            .filter(ApiCheck.timestamp >= start)
            .group_by(ApiCheck.provider)
            .order_by(ApiCheck.provider)
            .all()
        )

        total_checks = sum(r.total for r in rows) if rows else 0
        total_success = sum(r.successful or 0 for r in rows) if rows else 0
        overall_uptime = (total_success / total_checks * 100) if total_checks else 0.0

        lines = []
        lines.append("# AI API Weekly Reliability Report")
        lines.append("")
        lines.append(f"Generated (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Window (UTC): {start.strftime('%Y-%m-%d %H:%M:%S')} -> {now.strftime('%Y-%m-%d %H:%M:%S')}")
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
                uptime = (r.successful / r.total * 100) if r.total else 0.0
                lines.append(
                    f"| {r.provider} | {r.total} | {r.successful} | {pct(uptime)} | {ms(r.avg_latency)} | {ms(r.min_latency)} | {ms(r.max_latency)} |"
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
