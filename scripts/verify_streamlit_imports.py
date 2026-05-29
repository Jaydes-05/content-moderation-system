"""
Verification script to test Streamlit app imports.
"""

import sys
from pathlib import Path

# Simulate the path setup from dashboard/app.py
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Testing imports from dashboard/app.py...")
print(f"Project root: {project_root}")
print(f"Python path includes project root: {str(project_root) in sys.path}")

try:
    # Test the imports that were failing
    from api.database import (
        get_total_analyzed,
        get_today_analyzed,
        get_toxic_count,
        get_blocked_count,
        get_blocked_today,
        get_average_confidence,
        get_action_distribution,
        get_severity_distribution,
        get_recent_flagged
    )
    print("✓ All api.database imports successful")
    
    # Test that functions are callable
    print(f"✓ get_total_analyzed is callable: {callable(get_total_analyzed)}")
    
    print("\n✅ SUCCESS: All imports working correctly!")
    print("The Streamlit app should now start without ModuleNotFoundError")
    
except ImportError as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)
