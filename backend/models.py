"""
models.py — Database Schema Reference
======================================
The application uses raw SQLite (via sqlite3) rather than an ORM.
This file documents the three main tables for reference.

Tables
------
logs
    id                INTEGER  PRIMARY KEY AUTOINCREMENT
    user_id           TEXT
    login_time        TEXT     (HH:MM format)
    location          TEXT
    downloads         INTEGER
    failed_attempts   INTEGER
    status            TEXT     DEFAULT 'Active'
    ip_address        TEXT
    device_fingerprint TEXT

users
    id                INTEGER  PRIMARY KEY AUTOINCREMENT
    username          TEXT     UNIQUE NOT NULL
    email             TEXT     UNIQUE NOT NULL
    password_hash     TEXT     NOT NULL
    role              TEXT     DEFAULT 'Viewer'  -- Admin | Analyst | Viewer
    full_name         TEXT
    is_active         INTEGER  DEFAULT 1
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    last_login        TIMESTAMP

audit_logs
    id                INTEGER  PRIMARY KEY AUTOINCREMENT
    user_id           INTEGER  REFERENCES users(id)
    username          TEXT
    action            TEXT     NOT NULL
    resource          TEXT
    details           TEXT     (JSON)
    ip_address        TEXT
    timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP

revoked_tokens
    token_hash        TEXT     PRIMARY KEY
    revoked_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP

risk_thresholds
    id                INTEGER  PRIMARY KEY AUTOINCREMENT
    user_id           TEXT     (NULL = global default)
    threshold_type    TEXT
    threshold_value   INTEGER
    notification_enabled INTEGER DEFAULT 1
    notification_channels TEXT (JSON array)
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    UNIQUE(user_id, threshold_type)
"""
