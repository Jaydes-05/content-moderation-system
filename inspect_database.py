"""
Quick database inspector - view recent records and statistics.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api.database.db import (
    DB_PATH,
    get_db_connection,
    get_total_analyzed,
    get_today_analyzed,
    get_toxic_count,
    get_blocked_count,
    get_action_distribution,
    get_severity_distribution,
    get_recent_flagged
)
import json

def main():
    print("\n" + "="*80)
    print("  DATABASE INSPECTOR - Moderation History")
    print("="*80)
    
    print(f"\n📁 Database Location: {Path(DB_PATH).absolute()}")
    
    # Statistics
    print("\n📊 STATISTICS")
    print("-" * 80)
    total = get_total_analyzed()
    today = get_today_analyzed()
    toxic = get_toxic_count()
    blocked = get_blocked_count()
    
    print(f"Total Records:        {total:,}")
    print(f"Analyzed Today:       {today:,}")
    print(f"Toxic Content:        {toxic:,} ({toxic/total*100:.1f}%)" if total > 0 else "Toxic Content:        0")
    print(f"Blocked Content:      {blocked:,}")
    
    # Action Distribution
    print("\n🎯 ACTION DISTRIBUTION")
    print("-" * 80)
    actions = get_action_distribution()
    for action, count in sorted(actions.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(count / total * 50) if total > 0 else ""
        pct = count / total * 100 if total > 0 else 0
        print(f"{action:12} {count:5,} {bar:50} {pct:5.1f}%")
    
    # Severity Distribution
    print("\n⚠️  SEVERITY DISTRIBUTION")
    print("-" * 80)
    severity = get_severity_distribution()
    severity_order = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    for sev in severity_order:
        if sev in severity:
            count = severity[sev]
            bar = "█" * int(count / total * 50) if total > 0 else ""
            pct = count / total * 100 if total > 0 else 0
            print(f"{sev:12} {count:5,} {bar:50} {pct:5.1f}%")
    
    # Recent Flagged Content
    print("\n🚩 RECENT FLAGGED CONTENT (Last 10)")
    print("-" * 80)
    recent = get_recent_flagged(limit=10)
    
    if recent:
        for i, record in enumerate(recent, 1):
            text_preview = record['text'][:60] + "..." if len(record['text']) > 60 else record['text']
            print(f"\n{i}. [{record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}]")
            print(f"   Text: {text_preview}")
            print(f"   Action: {record['action']:8} | Severity: {record['severity']:8} | Confidence: {record['confidence']}%")
    else:
        print("No flagged content yet.")
    
    # Raw data sample
    print("\n📋 SAMPLE RECORDS (Last 5)")
    print("-" * 80)
    
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT id, input_text, moderation_action, severity, confidence, timestamp, is_toxic
        FROM moderation_history 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    if records:
        for record in records:
            text_preview = record['input_text'][:50] + "..." if len(record['input_text']) > 50 else record['input_text']
            toxic_flag = "🔴 TOXIC" if record['is_toxic'] else "🟢 CLEAN"
            print(f"\nID: {record['id']} | {toxic_flag}")
            print(f"Text: {text_preview}")
            print(f"Action: {record['moderation_action']} | Severity: {record['severity']} | Confidence: {record['confidence']:.2%}")
            print(f"Time: {record['timestamp']}")
    else:
        print("No records in database yet.")
    
    print("\n" + "="*80)
    print("✅ Database inspection complete!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
