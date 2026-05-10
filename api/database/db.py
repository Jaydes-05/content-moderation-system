"""
Database operations for moderation history storage.

This module provides functions for database connection management,
record insertion, and analytics queries.
"""

import sqlite3
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date

from api.database.models import SCHEMA_SQL, INDEX_SQL

logger = logging.getLogger(__name__)

# Database file path (relative to project root)
DB_PATH = "data/moderation_history.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Get a database connection with proper configuration.
    
    Returns:
        sqlite3.Connection: Configured database connection
    
    Raises:
        sqlite3.Error: If connection fails
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}, path: {DB_PATH}")
        raise


def init_database() -> None:
    """
    Initialize database and create tables if they don't exist.
    
    This function is idempotent and safe to call multiple times.
    Creates the data directory if it doesn't exist.
    
    Raises:
        sqlite3.Error: If database initialization fails
    """
    try:
        # Create data directory if it doesn't exist
        db_dir = Path(DB_PATH).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Connect and create schema
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create table
        cursor.executescript(SCHEMA_SQL)
        
        # Create indexes
        cursor.executescript(INDEX_SQL)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized successfully at {DB_PATH}")
    
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise


def insert_moderation_record(
    input_text: str,
    moderation_action: str,
    severity: str,
    primary_label: str,
    confidence: float,
    toxicity_scores: str,
    timestamp: str,
    is_toxic: bool
) -> int:
    """
    Insert a new moderation record into the database.
    
    Args:
        input_text: Original text that was moderated
        moderation_action: ALLOW, WARNING, HIDE, or BLOCK
        severity: NONE, LOW, MEDIUM, HIGH, or CRITICAL
        primary_label: Primary toxic category
        confidence: Confidence score (0.0-1.0)
        toxicity_scores: JSON string of all predictions
        timestamp: ISO 8601 timestamp
        is_toxic: Boolean flag (True/False, stored as 1/0)
    
    Returns:
        int: ID of the inserted record
    
    Raises:
        ValueError: If validation fails
        sqlite3.Error: If insertion fails
    """
    # Validate moderation_action
    if moderation_action not in ['ALLOW', 'WARNING', 'HIDE', 'BLOCK']:
        raise ValueError(f"Invalid moderation_action: {moderation_action}")
    
    # Validate severity
    if severity not in ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        raise ValueError(f"Invalid severity: {severity}")
    
    # Validate confidence
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(f"Confidence must be 0.0-1.0, got: {confidence}")
    
    # Validate JSON
    try:
        json.loads(toxicity_scores)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in toxicity_scores: {toxicity_scores}")
    
    # Validate required fields
    if not input_text:
        raise ValueError("input_text cannot be empty")
    if not primary_label:
        raise ValueError("primary_label cannot be empty")
    if not timestamp:
        raise ValueError("timestamp cannot be empty")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO moderation_history 
            (input_text, moderation_action, severity, primary_label, confidence, 
             toxicity_scores, timestamp, is_toxic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            input_text,
            moderation_action,
            severity,
            primary_label,
            confidence,
            toxicity_scores,
            timestamp,
            1 if is_toxic else 0
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.debug(f"Moderation record inserted with ID: {record_id}")
        return record_id
    
    except sqlite3.Error as e:
        logger.error(f"Database insertion failed: {e}")
        raise


def get_total_analyzed() -> int:
    """
    Get total count of analyzed comments.
    
    Returns:
        int: Total number of records
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM moderation_history")
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_total_analyzed): {e}")
        return 0


def get_today_analyzed() -> int:
    """
    Get count of comments analyzed today (UTC).
    
    Returns:
        int: Number of records from today
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT COUNT(*) FROM moderation_history 
            WHERE DATE(timestamp) = DATE('now')
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_today_analyzed): {e}")
        return 0


def get_toxic_count() -> int:
    """
    Get count of toxic comments (is_toxic = 1).
    
    Returns:
        int: Number of toxic records
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT COUNT(*) FROM moderation_history 
            WHERE is_toxic = 1
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_toxic_count): {e}")
        return 0


def get_blocked_count() -> int:
    """
    Get count of blocked comments (action = 'BLOCK').
    
    Returns:
        int: Number of blocked records
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT COUNT(*) FROM moderation_history 
            WHERE moderation_action = 'BLOCK'
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_blocked_count): {e}")
        return 0


def get_blocked_today() -> int:
    """
    Get count of comments blocked today (UTC).
    
    Returns:
        int: Number of records blocked today
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT COUNT(*) FROM moderation_history 
            WHERE moderation_action = 'BLOCK' 
            AND DATE(timestamp) = DATE('now')
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_blocked_today): {e}")
        return 0


def get_average_confidence() -> float:
    """
    Get average confidence score across all records.
    
    Returns:
        float: Average confidence (0.0-1.0), or 0.0 if no records
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT AVG(confidence) FROM moderation_history")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result is not None else 0.0
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_average_confidence): {e}")
        return 0.0


def get_action_distribution() -> Dict[str, int]:
    """
    Get distribution of moderation actions.
    
    Returns:
        Dict mapping action to count, e.g.:
        {'ALLOW': 13245, 'WARNING': 1234, 'HIDE': 912, 'BLOCK': 456}
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT moderation_action, COUNT(*) as count 
            FROM moderation_history 
            GROUP BY moderation_action
        """)
        
        result = {row['moderation_action']: row['count'] for row in cursor.fetchall()}
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_action_distribution): {e}")
        return {}


def get_severity_distribution() -> Dict[str, int]:
    """
    Get distribution of severity levels.
    
    Returns:
        Dict mapping severity to count, e.g.:
        {'NONE': 13245, 'LOW': 1234, 'MEDIUM': 856, 'HIGH': 412, 'CRITICAL': 100}
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT severity, COUNT(*) as count 
            FROM moderation_history 
            GROUP BY severity
        """)
        
        result = {row['severity']: row['count'] for row in cursor.fetchall()}
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_severity_distribution): {e}")
        return {}


def get_recent_flagged(limit: int = 10) -> List[Dict]:
    """
    Get N most recent flagged (toxic) comments.
    
    Args:
        limit: Maximum number of records to return (default 10)
    
    Returns:
        List of dicts with keys: timestamp, text, action, severity, confidence
        Ordered by timestamp descending (most recent first)
    """
    try:
        conn = get_db_connection()
        cursor = conn.execute("""
            SELECT timestamp, input_text, moderation_action, severity, confidence 
            FROM moderation_history 
            WHERE is_toxic = 1 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00')),
                'text': row['input_text'],
                'action': row['moderation_action'],
                'severity': row['severity'],
                'confidence': int(row['confidence'] * 100)  # Convert to 0-100 for display
            })
        
        conn.close()
        return results
    except sqlite3.Error as e:
        logger.error(f"Query failed (get_recent_flagged): {e}")
        return []
    except Exception as e:
        logger.error(f"Error processing recent flagged records: {e}")
        return []
