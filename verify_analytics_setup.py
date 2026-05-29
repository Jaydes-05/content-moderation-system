"""
Verification script for moderation history analytics setup.

This script checks that all components are properly installed and configured.

Usage:
    python verify_analytics_setup.py
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if os.path.isdir(dirpath):
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND: {dirpath}")
        return False

def check_import(module_path, description):
    """Check if a module can be imported."""
    try:
        parts = module_path.split('.')
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        print(f"✓ {description}: {module_path}")
        return True
    except ImportError as e:
        print(f"✗ {description} IMPORT FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ {description} ERROR: {e}")
        return False

def main():
    """Run verification checks."""
    print("=" * 70)
    print("MODERATION HISTORY ANALYTICS - SETUP VERIFICATION")
    print("=" * 70)
    print()
    
    all_checks_passed = True
    
    # Check database module files
    print("1. Database Module Files")
    print("-" * 70)
    all_checks_passed &= check_directory_exists("api/database", "Database module directory")
    all_checks_passed &= check_file_exists("api/database/__init__.py", "Database __init__.py")
    all_checks_passed &= check_file_exists("api/database/models.py", "Database models.py")
    all_checks_passed &= check_file_exists("api/database/db.py", "Database db.py")
    print()
    
    # Check data directory
    print("2. Data Directory")
    print("-" * 70)
    if not os.path.exists("data"):
        print("⚠ Data directory doesn't exist yet (will be created on first API startup)")
    else:
        all_checks_passed &= check_directory_exists("data", "Data directory")
        if os.path.exists("data/moderation_history.db"):
            print(f"✓ Database file exists: data/moderation_history.db")
            # Check database size
            size = os.path.getsize("data/moderation_history.db")
            print(f"  Database size: {size:,} bytes ({size/1024:.2f} KB)")
        else:
            print("⚠ Database file doesn't exist yet (will be created on first API startup)")
    print()
    
    # Check imports
    print("3. Python Imports")
    print("-" * 70)
    all_checks_passed &= check_import("api.database", "Database module")
    all_checks_passed &= check_import("api.database.db", "Database operations")
    all_checks_passed &= check_import("api.database.models", "Database models")
    print()
    
    # Check database functions
    print("4. Database Functions")
    print("-" * 70)
    try:
        from api.database import (
            init_database,
            insert_moderation_record,
            get_total_analyzed,
            get_today_analyzed,
            get_toxic_count,
            get_blocked_count,
            get_blocked_today,
            get_average_confidence,
            get_action_distribution,
            get_severity_distribution,
            get_recent_flagged,
        )
        print("✓ All database functions imported successfully")
        print("  - init_database")
        print("  - insert_moderation_record")
        print("  - get_total_analyzed")
        print("  - get_today_analyzed")
        print("  - get_toxic_count")
        print("  - get_blocked_count")
        print("  - get_blocked_today")
        print("  - get_average_confidence")
        print("  - get_action_distribution")
        print("  - get_severity_distribution")
        print("  - get_recent_flagged")
    except ImportError as e:
        print(f"✗ Failed to import database functions: {e}")
        all_checks_passed = False
    print()
    
    # Check FastAPI integration
    print("5. FastAPI Integration")
    print("-" * 70)
    try:
        with open("api/main.py", "r") as f:
            content = f.read()
            if "from api.database import init_database, insert_moderation_record" in content:
                print("✓ Database imports in api/main.py")
            else:
                print("✗ Database imports NOT FOUND in api/main.py")
                all_checks_passed = False
            
            if "init_database()" in content:
                print("✓ Database initialization in startup")
            else:
                print("✗ Database initialization NOT FOUND in startup")
                all_checks_passed = False
            
            if "insert_moderation_record(" in content:
                print("✓ Record insertion in /moderate endpoint")
            else:
                print("✗ Record insertion NOT FOUND in /moderate endpoint")
                all_checks_passed = False
    except Exception as e:
        print(f"✗ Error checking FastAPI integration: {e}")
        all_checks_passed = False
    print()
    
    # Check dashboard integration
    print("6. Dashboard Integration")
    print("-" * 70)
    try:
        with open("dashboard/app.py", "r") as f:
            content = f.read()
            if "fetch_analytics_data()" in content:
                print("✓ fetch_analytics_data() function exists")
            else:
                print("✗ fetch_analytics_data() function NOT FOUND")
                all_checks_passed = False
            
            if "from api.database.db import" in content:
                print("✓ Database imports in dashboard")
            else:
                print("✗ Database imports NOT FOUND in dashboard")
                all_checks_passed = False
    except Exception as e:
        print(f"✗ Error checking dashboard integration: {e}")
        all_checks_passed = False
    print()
    
    # Check test scripts
    print("7. Test Scripts")
    print("-" * 70)
    all_checks_passed &= check_file_exists("populate_test_data.py", "Test data population script")
    all_checks_passed &= check_file_exists("ANALYTICS_SETUP.md", "Setup documentation")
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    if all_checks_passed:
        print("✓ All checks passed!")
        print("\nNext steps:")
        print("1. Start the FastAPI backend:")
        print("   uvicorn api.main:app --reload")
        print("\n2. Populate test data:")
        print("   python populate_test_data.py")
        print("\n3. Start the dashboard:")
        print("   streamlit run dashboard/app.py")
        print("\n4. Navigate to Analytics Dashboard to see real data!")
    else:
        print("✗ Some checks failed. Please review the errors above.")
        print("\nRefer to ANALYTICS_SETUP.md for detailed setup instructions.")
    print("=" * 70)

if __name__ == "__main__":
    main()
