"""
Database schema definitions for moderation history.

This module contains SQL schema definitions for the SQLite database.
"""

# Database schema SQL
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS moderation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL,
    moderation_action TEXT NOT NULL CHECK(moderation_action IN ('ALLOW', 'WARNING', 'HIDE', 'BLOCK')),
    severity TEXT NOT NULL CHECK(severity IN ('NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    primary_label TEXT NOT NULL,
    confidence REAL NOT NULL CHECK(confidence >= 0.0 AND confidence <= 1.0),
    toxicity_scores TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    is_toxic INTEGER NOT NULL CHECK(is_toxic IN (0, 1))
);
"""

# Index definitions for query optimization
INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_timestamp ON moderation_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_is_toxic ON moderation_history(is_toxic);
CREATE INDEX IF NOT EXISTS idx_moderation_action ON moderation_history(moderation_action);
"""
