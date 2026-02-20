# quick_stats.py
from database import SessionLocal, ApiCheck
from sqlalchemy import func
from datetime import datetime, timedelta

db = SessionLocal()

# Get stats for last 24 hours
cutoff = datetime.utcnow() - timedelta(hours=24)

stats = db.query(
    ApiCheck.provider,
    func.count(ApiCheck.id).label('total'),
    func.sum(func.cast(ApiCheck.success, Integer)).label('successful'),
    func.avg(ApiCheck.latency_ms).label('avg_latency'),
    func.min(ApiCheck.latency_ms).label('min_latency'),
    func.max(ApiCheck.latency_ms).label('max_latency')
).filter(
    ApiCheck.timestamp >= cutoff
).group_by(
    ApiCheck.provider
).all()

print("\n" + "="*70)
print(f"📊 LAST 24 HOURS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print()

for stat in stats:
    uptime = (stat.successful / stat.total * 100) if stat.total > 0 else 0
    
    print(f"🔹 {stat.provider.upper()}")
    print(f"   Uptime:      {uptime:5.1f}% ({stat.successful}/{stat.total} checks)")
    print(f"   Avg Latency: {stat.avg_latency:6.0f}ms")
    print(f"   Min/Max:     {stat.min_latency:6.0f}ms / {stat.max_latency:6.0f}ms")
    print()

db.close()