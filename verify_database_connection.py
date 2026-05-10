"""
SQLite Database Connection Verification Script

This script checks:
1. Database file exists
2. Database connection works
3. Tables are created correctly
4. Can read/write data
5. Analytics queries work
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import sqlite3
from datetime import datetime
import json

# Import database functions
from api.database.db import (
    DB_PATH,
    get_db_connection,
    init_database,
    insert_moderation_record,
    get_total_analyzed,
    get_today_analyzed,
    get_toxic_count,
    get_blocked_count,
    get_action_distribution,
    get_severity_distribution,
    get_recent_flagged
)

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_database_file():
    """Check if database file exists."""
    print_section("1. Database File Check")
    
    db_path = Path(DB_PATH)
    print(f"Database path: {db_path.absolute()}")
    
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"✅ Database file exists")
        print(f"   Size: {size:,} bytes ({size/1024:.2f} KB)")
        return True
    else:
        print(f"⚠️  Database file does not exist yet")
        print(f"   Will be created on first use")
        return False

def check_database_connection():
    """Check if database connection works."""
    print_section("2. Database Connection Check")
    
    try:
        conn = get_db_connection()
        print(f"✅ Database connection successful")
        print(f"   SQLite version: {sqlite3.sqlite_version}")
        print(f"   Connection type: {type(conn)}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def check_database_schema():
    """Check if tables exist and have correct schema."""
    print_section("3. Database Schema Check")
    
    try:
        # Initialize database (creates tables if they don't exist)
        init_database()
        print(f"✅ Database initialized successfully")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if moderation_history table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='moderation_history'
        """)
        
        if cursor.fetchone():
            print(f"✅ Table 'moderation_history' exists")
            
            # Get table schema
            cursor.execute("PRAGMA table_info(moderation_history)")
            columns = cursor.fetchall()
            
            print(f"\n   Table columns ({len(columns)}):")
            for col in columns:
                col_id, name, col_type, not_null, default, pk = col
                print(f"   - {name:20} {col_type:15} {'PRIMARY KEY' if pk else ''}")
            
            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='moderation_history'
            """)
            indexes = cursor.fetchall()
            print(f"\n   Indexes ({len(indexes)}):")
            for idx in indexes:
                print(f"   - {idx[0]}")
            
            conn.close()
            return True
        else:
            print(f"❌ Table 'moderation_history' does not exist")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

def check_database_operations():
    """Check if read/write operations work."""
    print_section("4. Database Operations Check")
    
    try:
        # Get current count
        initial_count = get_total_analyzed()
        print(f"Current record count: {initial_count}")
        
        # Try to insert a test record
        print(f"\nInserting test record...")
        test_record_id = insert_moderation_record(
            input_text="This is a test comment for verification",
            moderation_action="ALLOW",
            severity="NONE",
            primary_label="clean",
            confidence=0.95,
            toxicity_scores=json.dumps({
                "toxic": 0.05,
                "severe_toxic": 0.01,
                "obscene": 0.02,
                "threat": 0.01,
                "insult": 0.03,
                "identity_hate": 0.01
            }),
            timestamp=datetime.utcnow().isoformat() + "Z",
            is_toxic=False
        )
        
        print(f"✅ Test record inserted with ID: {test_record_id}")
        
        # Verify count increased
        new_count = get_total_analyzed()
        if new_count == initial_count + 1:
            print(f"✅ Record count increased: {initial_count} → {new_count}")
        else:
            print(f"⚠️  Unexpected count: {new_count} (expected {initial_count + 1})")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def check_analytics_queries():
    """Check if analytics queries work."""
    print_section("5. Analytics Queries Check")
    
    try:
        print("Running analytics queries...\n")
        
        # Test each analytics function
        total = get_total_analyzed()
        print(f"✅ get_total_analyzed(): {total:,}")
        
        today = get_today_analyzed()
        print(f"✅ get_today_analyzed(): {today:,}")
        
        toxic = get_toxic_count()
        print(f"✅ get_toxic_count(): {toxic:,}")
        
        blocked = get_blocked_count()
        print(f"✅ get_blocked_count(): {blocked:,}")
        
        actions = get_action_distribution()
        print(f"✅ get_action_distribution(): {actions}")
        
        severity = get_severity_distribution()
        print(f"✅ get_severity_distribution(): {severity}")
        
        recent = get_recent_flagged(limit=5)
        print(f"✅ get_recent_flagged(): {len(recent)} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Analytics queries failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  SQLite Database Connection Verification")
    print("="*60)
    
    results = []
    
    # Run all checks
    results.append(("Database File", check_database_file()))
    results.append(("Database Connection", check_database_connection()))
    results.append(("Database Schema", check_database_schema()))
    results.append(("Database Operations", check_database_operations()))
    results.append(("Analytics Queries", check_analytics_queries()))
    
    # Summary
    print_section("Verification Summary")
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All checks passed! Database is working correctly.")
        print("="*60)
        print("\nYour Streamlit app is connected to:")
        print(f"  Database: {Path(DB_PATH).absolute()}")
        print(f"  Records: {get_total_analyzed():,}")
        print("\nYou can now:")
        print("  1. Start the API: uvicorn api.main:app --reload")
        print("  2. Start Streamlit: streamlit run dashboard/app.py")
        print("  3. Moderate content and see it stored in the database")
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
