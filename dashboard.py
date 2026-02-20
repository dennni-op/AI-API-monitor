# api.py (dashboard)
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database import SessionLocal, ApiCheck
from sqlalchemy import func, Integer
from datetime import datetime, timedelta, date

app = FastAPI(title="AI API Status Monitor")


@app.get("/api/status")
def get_status():
    """Get current status (last hour)"""
    db = SessionLocal()
    cutoff = datetime.now() - timedelta(hours=1)

    stats = db.query(
        ApiCheck.provider,
        func.count(ApiCheck.id).label('total'),
        func.sum(func.cast(ApiCheck.success, Integer)).label('successful'),
        func.avg(ApiCheck.latency_ms).label('avg_latency')
    ).filter(
        ApiCheck.timestamp >= cutoff
    ).group_by(ApiCheck.provider).all()

    results = []
    for stat in stats:
        uptime = (stat.successful / stat.total * 100) if stat.total > 0 else 0
        results.append({
            'provider': stat.provider,
            'uptime': round(uptime, 1),
            'avg_latency': round(stat.avg_latency, 0) if stat.avg_latency else 0,
            'checks': stat.total
        })

    db.close()
    return results


@app.get("/api/history")
def get_history(days: int = 90):
    """Return per-day uptime summary for the last `days` days for each provider."""
    db = SessionLocal()
    end = datetime.now().date()
    start = end - timedelta(days=days - 1)

    # Query counts grouped by provider and date
    stats = db.query(
        ApiCheck.provider,
        func.date(ApiCheck.timestamp).label('day'),
        func.count(ApiCheck.id).label('total'),
        func.sum(func.cast(ApiCheck.success, Integer)).label('successful')
    ).filter(
        ApiCheck.timestamp >= datetime.combine(start, datetime.min.time())
    ).group_by(ApiCheck.provider, func.date(ApiCheck.timestamp)).all()

    # Organize results by provider and fill missing days
    providers = {}
    for row in stats:
        prov = row.provider
        day = row.day
        total = row.total
        successful = row.successful or 0
        uptime = (successful / total * 100) if total > 0 else 0
        providers.setdefault(prov, {})[day] = round(uptime, 1)

    # Build array of days
    days_list = [(start + timedelta(days=i)) for i in range(days)]

    result = []
    for prov, day_map in providers.items():
        timeline = []
        for d in days_list:
            val = day_map.get(d, None)
            # treat missing as 100% if no checks? we'll display as 'no-data' so front-end can show neutral
            timeline.append({
                'date': d.isoformat(),
                'uptime': val
            })
        result.append({'provider': prov, 'timeline': timeline})

    db.close()
    return {'start': start.isoformat(), 'end': end.isoformat(), 'data': result}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Enhanced dashboard with 90-day timeline similar to GitHub Status"""
    return """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>AI API Status</title>
      <style>
        :root{--bg:#0b1220;--card:#0f1724;--muted:#94a3b8;--accent:#60a5fa}
        *{box-sizing:border-box}
        body{font-family:Inter,ui-sans-serif,system-ui,-apple-system; background:var(--bg); color:#e6eef8; margin:0;padding:24px}
        .container{max-width:1200px;margin:0 auto}
        header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:24px}
        h1{font-size:28px;margin:0;color:var(--accent)}
        .subtitle{color:var(--muted)}
        .grid{display:grid;grid-template-columns:1fr 320px;gap:20px}
        .left{min-width:0}
        .right{min-width:0}
        .component-list{display:flex;flex-direction:column;gap:12px}
        .component{background:var(--card);padding:16px;border-radius:8px;border:1px solid #233045}
        .component h3{margin:0 0 8px 0;font-size:16px}
        .small{font-size:13px;color:var(--muted)}
        .timeline{display:flex;gap:2px;flex-wrap:wrap}
        .day{width:8px;height:18px;border-radius:2px;display:inline-block}
        .green{background:#10b981}
        .yellow{background:#f59e0b}
        .red{background:#ef4444}
        .neutral{background:#1f2937}
        .legend{display:flex;gap:10px;align-items:center;margin-top:10px}
        .legend .item{display:flex;gap:6px;align-items:center}
        .legend .sw{width:12px;height:12px;border-radius:2px}
        footer{margin-top:20px;color:var(--muted);font-size:13px}
        @media (max-width:900px){.grid{grid-template-columns:1fr}}
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <div>
            <h1>AI API Status</h1>
            <div class="subtitle">Independent monitoring of OpenAI, Anthropic, and Google AI APIs</div>
          </div>
          <div class="small">Updated: <span id="last-updated">--</span></div>
        </header>

        <div class="grid">
          <div class="left">
            <div id="timeline-area"></div>
          </div>

          <aside class="right">
            <div class="component-list" id="components">
              <div class="component">Loading...</div>
            </div>
          </aside>
        </div>

        <footer>
          Built by Dennis • Data from local checks
        </footer>
      </div>

      <script>
        function colorClass(uptime){
          if (uptime === null || uptime === undefined) return 'neutral'
          if (uptime >= 99) return 'green'
          if (uptime >= 95) return 'yellow'
          return 'red'
        }

        async function loadAll(){
          try{
            const [statusRes, histRes] = await Promise.all([fetch('/api/status'), fetch('/api/history')]);
            const status = await statusRes.json();
            const hist = await histRes.json();

            document.getElementById('last-updated').textContent = new Date().toLocaleString();

            // Components box
            const compBox = document.getElementById('components');
            compBox.innerHTML = '';
            status.forEach(p => {
              const el = document.createElement('div'); el.className='component';
              const statusDot = p.uptime >= 99 ? '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#10b981;margin-right:8px"></span>' : p.uptime >=95 ? '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#f59e0b;margin-right:8px"></span>' : '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#ef4444;margin-right:8px"></span>'
              el.innerHTML = `<h3>${statusDot} ${p.provider}</h3><div class="small">Uptime (1h): <strong>${p.uptime}%</strong></div><div class="small">Avg latency: ${p.avg_latency}ms</div>`
              compBox.appendChild(el)
            })

            // Timeline area
            const tArea = document.getElementById('timeline-area');
            tArea.innerHTML = '';
            const header = document.createElement('div'); header.className='small'; header.textContent = `Showing ${hist.start} → ${hist.end}`
            tArea.appendChild(header)

            hist.data.forEach(group => {
              const row = document.createElement('div'); row.style.margin='12px 0';
              const title = document.createElement('div'); title.style.marginBottom='6px'; title.innerHTML = `<strong>${group.provider}</strong>`
              const timeline = document.createElement('div'); timeline.className='timeline';

              group.timeline.forEach(day => {
                const d = document.createElement('span'); d.className='day ' + colorClass(day.uptime); d.title = `${day.date} • ${day.uptime===null? 'no checks' : day.uptime+'%'} `
                timeline.appendChild(d);
              })

              row.appendChild(title); row.appendChild(timeline);
              tArea.appendChild(row);
            })

            // legend
            const legend = document.createElement('div'); legend.className='legend';
            legend.innerHTML = `<div class="item"><span class="sw" style="background:#10b981"></span> Operational</div><div class="item"><span class="sw" style="background:#f59e0b"></span> Degraded</div><div class="item"><span class="sw" style="background:#ef4444"></span> Major Outage</div><div class="item"><span class="sw" style="background:#1f2937"></span> No Data</div>`
            tArea.appendChild(legend)

          }catch(e){
            console.error(e);
            document.getElementById('components').innerHTML = '<div class="component">Error loading data</div>'
          }
        }

        loadAll();
        setInterval(loadAll, 60_000);
      </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)