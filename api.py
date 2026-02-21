from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database import SessionLocal, ApiCheck, init_db
from sqlalchemy import func, case
from datetime import datetime, timedelta

app = FastAPI(title="AI API Status Monitor")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/api/status")
def get_status():
    """Get current status (last hour)"""
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(hours=1)
    
    stats = db.query(
        ApiCheck.provider,
        func.count(ApiCheck.id).label('total'),
        func.sum(
            case(
                (ApiCheck.success == True, 1),
                else_=0
            )
        ).label('successful'),
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
        func.sum(
            case(
                (ApiCheck.success == True, 1),
                else_=0
            )
        ).label('successful')
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
            'date': stat.date.isoformat() if hasattr(stat.date, 'isoformat') else str(stat.date),
            'uptime': round(uptime, 1)
        })
    
    db.close()
    return history

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """GitHub-inspired status dashboard with expandable details"""
    # [Keep your existing HTML here - no changes needed]
    return """
    [Your existing dashboard HTML - too long to paste, keep as is]
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)