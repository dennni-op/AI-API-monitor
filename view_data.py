# view_data.py
from database import SessionLocal, ApiCheck
from sqlalchemy import func, Integer

def show_all_checks():
    """Show all checks"""
    db = SessionLocal()
    
    checks = db.query(ApiCheck).order_by(ApiCheck.timestamp.desc()).limit(20).all()
    
    print("\n" + "="*70)
    print("RECENT CHECKS (Last 20)")
    print("="*70)
    print(f"{'Time':20s} {'Provider':12s} {'Model':25s} {'Latency':>10s} {'Status':>8s}")
    print("-"*70)
    
    for check in checks:
        status = "✅" if check.success else "❌"
        latency = f"{check.latency_ms:.0f}ms" if check.success else "FAILED"
        print(f"{check.timestamp.strftime('%Y-%m-%d %H:%M:%S'):20s} "
              f"{check.provider:12s} "
              f"{check.model:25s} "
              f"{latency:>10s} "
              f"{status:>8s}")
    
    db.close()

def show_stats():
    """Show statistics"""
    db = SessionLocal()
    
    stats = db.query(
        ApiCheck.provider,
        func.count(ApiCheck.id).label('total'),
        func.sum(func.cast(ApiCheck.success, Integer)).label('successful'),
        func.avg(ApiCheck.latency_ms).label('avg_latency')
    ).group_by(ApiCheck.provider).all()
    
    print("\n" + "="*70)
    print("OVERALL STATISTICS")
    print("="*70)
    print(f"{'Provider':12s} {'Total':>8s} {'Success':>8s} {'Uptime':>8s} {'Avg Latency':>12s}")
    print("-"*70)
    
    for stat in stats:
        uptime = (stat.successful / stat.total * 100) if stat.total > 0 else 0
        avg_lat = f"{stat.avg_latency:.0f}ms" if stat.avg_latency else "N/A"
        print(f"{stat.provider:12s} "
              f"{stat.total:8d} "
              f"{stat.successful:8d} "
              f"{uptime:7.1f}% "
              f"{avg_lat:>12s}")
    
    print()
    db.close()

if __name__ == "__main__":
    show_all_checks()
    show_stats()