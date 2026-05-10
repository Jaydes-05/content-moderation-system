"""
Database module for moderation history storage.

This module provides SQLite-based persistence for moderation records
and analytics query operations.
"""

from api.database.db import (
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

__all__ = [
    'init_database',
    'insert_moderation_record',
    'get_total_analyzed',
    'get_today_analyzed',
    'get_toxic_count',
    'get_blocked_count',
    'get_blocked_today',
    'get_average_confidence',
    'get_action_distribution',
    'get_severity_distribution',
    'get_recent_flagged',
]
