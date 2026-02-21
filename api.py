# api.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database import SessionLocal, ApiCheck
from sqlalchemy import func, Integer
from datetime import datetime, timedelta

app = FastAPI(title="AI API Status Monitor")

@app.get("/api/status")
def get_status():
    """Get current status (last hour)"""
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(hours=1)
    
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
            'checks': stat.total,
            'status': 'operational' if uptime >= 99 else 'degraded' if uptime >= 95 else 'major_outage'
        })
    
    db.close()
    return results

@app.get("/api/recent-checks/{provider}")
def get_recent_checks(provider: str, hours: int = 24):
    """Get recent checks for a provider (last 24 hours)"""
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    checks = db.query(ApiCheck).filter(
        ApiCheck.provider == provider,
        ApiCheck.timestamp >= cutoff
    ).order_by(
        ApiCheck.timestamp.desc()
    ).limit(100).all()
    
    results = []
    for check in checks:
        results.append({
            'timestamp': check.timestamp.isoformat(),
            'success': check.success,
            'latency_ms': round(check.latency_ms, 0) if check.success else None,
            'error': check.error_message if not check.success else None
        })
    
    db.close()
    return results

@app.get("/api/uptime-history/{provider}")
def get_uptime_history(provider: str, days: int = 90):
    """Get daily uptime history for sparkline"""
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    daily_stats = db.query(
        func.date(ApiCheck.timestamp).label('date'),
        func.count(ApiCheck.id).label('total'),
        func.sum(func.cast(ApiCheck.success, Integer)).label('successful')
    ).filter(
        ApiCheck.provider == provider,
        ApiCheck.timestamp >= cutoff
    ).group_by(
        func.date(ApiCheck.timestamp)
    ).order_by(
        func.date(ApiCheck.timestamp)
    ).all()
    
    history = []
    for stat in daily_stats:
        uptime = (stat.successful / stat.total * 100) if stat.total > 0 else 0
        history.append({
            'date': stat.date.isoformat(),
            'uptime': round(uptime, 1)
        })
    
    db.close()
    return history

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """GitHub-inspired status dashboard with expandable details"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI API Status Monitor</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica', 'Arial', sans-serif;
                background: #f6f8fa;
                color: #24292f;
                padding: 40px 20px;
                line-height: 1.5;
            }
            
            .container {
                max-width: 1280px;
                margin: 0 auto;
            }
            
            header {
                margin-bottom: 32px;
            }
            
            h1 {
                font-size: 32px;
                font-weight: 600;
                color: #24292f;
                margin-bottom: 8px;
            }
            
            .subtitle {
                color: #57606a;
                font-size: 16px;
            }
            
            .status-grid {
                display: grid;
                gap: 1px;
                background: #d0d7de;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .component {
                background: white;
                transition: all 0.2s;
            }
            
            .component-header {
                padding: 16px;
                display: grid;
                grid-template-columns: 200px 1fr 100px;
                gap: 16px;
                align-items: center;
                cursor: pointer;
                user-select: none;
            }
            
            .component-header:hover {
                background: #f6f8fa;
            }
            
            .component-name {
                font-size: 16px;
                font-weight: 600;
                color: #24292f;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .expand-icon {
                font-size: 12px;
                color: #57606a;
                transition: transform 0.2s;
            }
            
            .component.expanded .expand-icon {
                transform: rotate(90deg);
            }
            
            .status-indicator {
                width: 18px;
                height: 18px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .status-indicator.operational {
                background: #1a7f37;
            }
            
            .status-indicator.degraded {
                background: #fb8500;
            }
            
            .status-indicator.major_outage {
                background: #cf222e;
            }
            
            .status-indicator svg {
                width: 12px;
                height: 12px;
                fill: white;
            }
            
            .uptime-bar {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .uptime-graph {
                flex: 1;
                height: 34px;
                display: flex;
                gap: 1px;
                align-items: flex-end;
            }
            
            .uptime-day {
                flex: 1;
                min-width: 2px;
                background: #1a7f37;
                transition: all 0.2s;
                cursor: pointer;
                position: relative;
            }
            
            .uptime-day.degraded { background: #fb8500; }
            .uptime-day.major_outage { background: #cf222e; }
            .uptime-day.no-data { background: #d0d7de; }
            
            .uptime-day:hover {
                opacity: 0.8;
                transform: scaleY(1.1);
            }
            
            .timeline-labels {
                display: flex;
                justify-content: space-between;
                font-size: 11px;
                color: #57606a;
                margin-top: 4px;
            }
            
            .status-text {
                font-size: 14px;
                color: #57606a;
                text-align: right;
            }
            
            .status-text.operational { color: #1a7f37; }
            .status-text.degraded { color: #fb8500; }
            .status-text.major_outage { color: #cf222e; }
            
            .metrics {
                display: flex;
                gap: 16px;
                font-size: 12px;
                color: #57606a;
                margin-top: 4px;
            }
            
            .metric-item {
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            /* Expandable details section */
            .component-details {
                max-height: 0;
                overflow: hidden;
                transition: max-height 0.3s ease-out;
                background: #f6f8fa;
                border-top: 1px solid #d0d7de;
            }
            
            .component.expanded .component-details {
                max-height: 2000px;
            }
            
            .details-content {
                padding: 16px;
            }
            
            .details-header {
                font-size: 14px;
                font-weight: 600;
                color: #24292f;
                margin-bottom: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .checks-table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 6px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .checks-table th {
                background: #f6f8fa;
                padding: 12px 16px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                color: #57606a;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .checks-table td {
                padding: 12px 16px;
                border-top: 1px solid #d0d7de;
                font-size: 14px;
            }
            
            .checks-table tr:hover {
                background: #f6f8fa;
            }
            
            .check-status {
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            
            .check-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }
            
            .check-dot.success { background: #1a7f37; }
            .check-dot.failure { background: #cf222e; }
            
            .latency-good { color: #1a7f37; font-weight: 600; }
            .latency-ok { color: #fb8500; font-weight: 600; }
            .latency-bad { color: #cf222e; font-weight: 600; }
            
            .error-message {
                color: #cf222e;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
            
            .footer {
                text-align: center;
                color: #57606a;
                margin-top: 32px;
                padding-top: 16px;
                border-top: 1px solid #d0d7de;
                font-size: 14px;
            }
            
            .last-updated {
                display: inline-block;
                color: #57606a;
                font-size: 12px;
                margin-bottom: 16px;
            }
            
            .loading {
                text-align: center;
                padding: 60px 20px;
                font-size: 16px;
                color: #57606a;
            }
            
            .details-loading {
                text-align: center;
                padding: 20px;
                color: #57606a;
                font-size: 14px;
            }
            
            @media (max-width: 768px) {
                .component-header {
                    grid-template-columns: 1fr;
                    gap: 12px;
                }
                
                .status-text {
                    text-align: left;
                }
                
                .checks-table {
                    font-size: 12px;
                }
                
                .checks-table th,
                .checks-table td {
                    padding: 8px 12px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Current Status: AI API Monitor</h1>
                <p class="subtitle">Uptime over the past 90 days • Click provider to see recent checks</p>
            </header>
            
            <div class="last-updated" id="last-updated">Loading...</div>
            
            <div id="status-grid" class="status-grid">
                <div class="loading">Loading status data...</div>
            </div>
            
            <div class="footer">
                <p>Checks run every hour • Independent monitoring</p>
                <p style="margin-top: 8px; font-size: 12px;">Built by Dennis</p>
            </div>
        </div>
        
        <script>
            let expandedProvider = null;
            
            async function loadStatus() {
                try {
                    const response = await fetch('/api/status');
                    const providers = await response.json();
                    
                    const grid = document.getElementById('status-grid');
                    
                    if (providers.length === 0) {
                        grid.innerHTML = '<div class="loading">No data yet. Checks running every hour.</div>';
                        return;
                    }
                    
                    document.getElementById('last-updated').textContent = 
                        `Last updated: ${new Date().toLocaleTimeString()}`;
                    
                    let html = '';
                    
                    for (const provider of providers) {
                        const uptimeBars = await generateUptimeBars(provider.provider);
                        const statusClass = provider.status;
                        const statusText = provider.status === 'operational' ? 'Operational' :
                                         provider.status === 'degraded' ? 'Degraded Performance' :
                                         'Major Outage';
                        
                        const checkmark = provider.status === 'operational' ? 
                            '<svg viewBox="0 0 16 16"><path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"></path></svg>' : '';
                        
                        const isExpanded = expandedProvider === provider.provider;
                        
                        html += `
                            <div class="component ${isExpanded ? 'expanded' : ''}" data-provider="${provider.provider}">
                                <div class="component-header" onclick="toggleDetails('${provider.provider}')">
                                    <div class="component-name">
                                        <span class="expand-icon">▶</span>
                                        <div class="status-indicator ${statusClass}">
                                            ${checkmark}
                                        </div>
                                        <span>${capitalizeProvider(provider.provider)}</span>
                                    </div>
                                    
                                    <div>
                                        <div class="uptime-bar">
                                            <div class="uptime-graph">
                                                ${uptimeBars}
                                            </div>
                                        </div>
                                        <div class="timeline-labels">
                                            <span>90 days ago</span>
                                            <span>Today</span>
                                        </div>
                                        <div class="metrics">
                                            <span class="metric-item">⚡ ${provider.avg_latency}ms avg</span>
                                            <span class="metric-item">📊 ${provider.uptime}% uptime</span>
                                            <span class="metric-item">✓ ${provider.checks} checks</span>
                                        </div>
                                    </div>
                                    
                                    <div class="status-text ${statusClass}">
                                        ${statusText}
                                    </div>
                                </div>
                                
                                <div class="component-details">
                                    <div class="details-content" id="details-${provider.provider}">
                                        ${isExpanded ? await loadRecentChecks(provider.provider) : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    grid.innerHTML = html;
                    
                } catch (error) {
                    console.error('Error loading status:', error);
                    document.getElementById('status-grid').innerHTML = 
                        '<div class="loading">Error loading data</div>';
                }
            }
            
            async function toggleDetails(provider) {
                const component = document.querySelector(`[data-provider="${provider}"]`);
                const isExpanded = component.classList.contains('expanded');
                
                // Close all other expanded components
                document.querySelectorAll('.component.expanded').forEach(el => {
                    if (el !== component) {
                        el.classList.remove('expanded');
                    }
                });
                
                if (isExpanded) {
                    component.classList.remove('expanded');
                    expandedProvider = null;
                } else {
                    component.classList.add('expanded');
                    expandedProvider = provider;
                    
                    // Load recent checks
                    const detailsDiv = document.getElementById(`details-${provider}`);
                    detailsDiv.innerHTML = '<div class="details-loading">Loading recent checks...</div>';
                    
                    const checksHtml = await loadRecentChecks(provider);
                    detailsDiv.innerHTML = checksHtml;
                }
            }
            
            async function loadRecentChecks(provider) {
                try {
                    const response = await fetch(`/api/recent-checks/${provider}?hours=24`);
                    const checks = await response.json();
                    
                    if (checks.length === 0) {
                        return '<div class="details-loading">No checks in the last 24 hours</div>';
                    }
                    
                    let html = `
                        <div class="details-header">
                            <span>Recent Checks (Last 24 Hours)</span>
                            <span style="font-weight: normal; color: #57606a;">${checks.length} total checks</span>
                        </div>
                        <table class="checks-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Status</th>
                                    <th>Latency</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    for (const check of checks) {
                        const time = new Date(check.timestamp);
                        const timeStr = time.toLocaleTimeString() + ' ' + time.toLocaleDateString();
                        
                        const statusHtml = check.success ? 
                            '<span class="check-status"><span class="check-dot success"></span>Success</span>' :
                            '<span class="check-status"><span class="check-dot failure"></span>Failed</span>';
                        
                        let latencyClass = '';
                        let latencyStr = '';
                        if (check.success) {
                            if (check.latency_ms < 1000) {
                                latencyClass = 'latency-good';
                            } else if (check.latency_ms < 2000) {
                                latencyClass = 'latency-ok';
                            } else {
                                latencyClass = 'latency-bad';
                            }
                            latencyStr = `<span class="${latencyClass}">${check.latency_ms}ms</span>`;
                        } else {
                            latencyStr = '<span style="color: #57606a;">-</span>';
                        }
                        
                        const details = check.error ? 
                            `<span class="error-message">${check.error.substring(0, 100)}${check.error.length > 100 ? '...' : ''}</span>` :
                            '<span style="color: #1a7f37;">✓ Operational</span>';
                        
                        html += `
                            <tr>
                                <td>${timeStr}</td>
                                <td>${statusHtml}</td>
                                <td>${latencyStr}</td>
                                <td>${details}</td>
                            </tr>
                        `;
                    }
                    
                    html += `
                            </tbody>
                        </table>
                    `;
                    
                    return html;
                    
                } catch (error) {
                    console.error('Error loading recent checks:', error);
                    return '<div class="details-loading">Error loading checks</div>';
                }
            }
            
            async function generateUptimeBars(provider) {
                try {
                    const response = await fetch(`/api/uptime-history/${provider}?days=90`);
                    const history = await response.json();
                    
                    if (history.length === 0) {
                        let bars = '';
                        for (let i = 0; i < 90; i++) {
                            bars += '<div class="uptime-day no-data" style="height: 100%"></div>';
                        }
                        return bars;
                    }
                    
                    let bars = '';
                    for (const day of history) {
                        const statusClass = day.uptime >= 99 ? 'operational' :
                                          day.uptime >= 95 ? 'degraded' :
                                          day.uptime >= 50 ? 'major_outage' : 'major_outage';
                        
                        bars += `<div class="uptime-day ${statusClass}" 
                                     style="height: ${day.uptime}%" 
                                     title="${day.date}: ${day.uptime}% uptime"></div>`;
                    }
                    
                    for (let i = history.length; i < 90; i++) {
                        bars += '<div class="uptime-day no-data" style="height: 100%"></div>';
                    }
                    
                    return bars;
                    
                } catch (error) {
                    let bars = '';
                    for (let i = 0; i < 90; i++) {
                        bars += '<div class="uptime-day no-data" style="height: 100%"></div>';
                    }
                    return bars;
                }
            }
            
            function capitalizeProvider(name) {
                const names = {
                    'google': 'Google Gemini 2.5 Flash',
                    'openai': 'OpenAI GPT-4.1 Mini',
                    'anthropic': 'Anthropic Claude 4.6 Opus'
                };
                return names[name] || name.charAt(0).toUpperCase() + name.slice(1);
            }
            
            loadStatus();
            setInterval(loadStatus, 60000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)