-- Session Memory System Schema
-- Hybrid approach: JSONL (source of truth) + SQLite (fast queries)
-- Created: 2025-10-29

-- ============================================================================
-- SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,           -- UUID
    start_time TIMESTAMP NOT NULL,         -- ISO-8601
    end_time TIMESTAMP,                    -- NULL if ongoing
    title TEXT NOT NULL,                   -- User-provided or auto-generated
    description TEXT,                      -- Brief summary
    status TEXT CHECK(status IN ('active', 'paused', 'completed', 'abandoned')),
    context TEXT,                          -- What was I working on?
    branch TEXT,                           -- Git branch
    commit_hash TEXT,                      -- Git commit at session start
    persona TEXT,                          -- Which persona was active
    parent_session_id TEXT,                -- For continuation of previous work
    resonance_score REAL,                  -- 0.0-1.0, how successful was this session
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(session_id)
);

-- Index for chronological queries
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_persona ON sessions(persona);

-- ============================================================================
-- TASKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,              -- UUID
    session_id TEXT NOT NULL,              -- Foreign key to sessions
    task_number INTEGER NOT NULL,          -- 1, 2, 3... within session
    title TEXT NOT NULL,                   -- What was done
    description TEXT,                      -- Details
    status TEXT CHECK(status IN ('not-started', 'in-progress', 'completed', 'blocked')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,              -- Calculated on completion
    result TEXT,                           -- Success, partial, failed
    notes TEXT,                            -- Free-form notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Index for session lookups
CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id, task_number);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- ============================================================================
-- ARTIFACTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,          -- UUID
    session_id TEXT NOT NULL,              -- Foreign key to sessions
    task_id TEXT,                          -- Optional: which task created this
    artifact_type TEXT NOT NULL,           -- 'file', 'code', 'script', 'doc', 'data'
    file_path TEXT,                        -- Absolute path (if file)
    relative_path TEXT,                    -- Relative to workspace
    content_hash TEXT,                     -- SHA256 for change detection
    file_size_bytes INTEGER,
    operation TEXT,                        -- 'created', 'modified', 'deleted'
    description TEXT,                      -- What is this artifact
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE SET NULL
);

-- Index for file lookups
CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_file_path ON artifacts(file_path);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);

-- ============================================================================
-- TAGS TABLE (for flexible categorization)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT UNIQUE NOT NULL
);

-- ============================================================================
-- SESSION_TAGS (many-to-many relationship)
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_tags (
    session_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, tag_id),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_tags_tag ON session_tags(tag_id);

-- ============================================================================
-- FULL-TEXT SEARCH (FTS5)
-- ============================================================================
-- Virtual table for fast text search across sessions, tasks, artifacts
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
    session_id UNINDEXED,
    title,
    description,
    context,
    content='sessions',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS sessions_fts_insert AFTER INSERT ON sessions
BEGIN
    INSERT INTO sessions_fts(rowid, session_id, title, description, context)
    VALUES (new.rowid, new.session_id, new.title, new.description, new.context);
END;

CREATE TRIGGER IF NOT EXISTS sessions_fts_update AFTER UPDATE ON sessions
BEGIN
    UPDATE sessions_fts SET title = new.title, description = new.description, context = new.context
    WHERE rowid = new.rowid;
END;

CREATE TRIGGER IF NOT EXISTS sessions_fts_delete AFTER DELETE ON sessions
BEGIN
    DELETE FROM sessions_fts WHERE rowid = old.rowid;
END;

-- FTS for tasks
CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(
    task_id UNINDEXED,
    title,
    description,
    notes,
    content='tasks',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS tasks_fts_insert AFTER INSERT ON tasks
BEGIN
    INSERT INTO tasks_fts(rowid, task_id, title, description, notes)
    VALUES (new.rowid, new.task_id, new.title, new.description, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS tasks_fts_update AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks_fts SET title = new.title, description = new.description, notes = new.notes
    WHERE rowid = new.rowid;
END;

CREATE TRIGGER IF NOT EXISTS tasks_fts_delete AFTER DELETE ON tasks
BEGIN
    DELETE FROM tasks_fts WHERE rowid = old.rowid;
END;

-- ============================================================================
-- VIEWS (for common queries)
-- ============================================================================

-- Recent sessions with task count
CREATE VIEW IF NOT EXISTS v_recent_sessions AS
SELECT 
    s.session_id,
    s.start_time,
    s.end_time,
    s.title,
    s.status,
    s.persona,
    s.resonance_score,
    COUNT(DISTINCT t.task_id) as task_count,
    COUNT(DISTINCT a.artifact_id) as artifact_count,
    GROUP_CONCAT(DISTINCT tg.tag_name) as tags
FROM sessions s
LEFT JOIN tasks t ON s.session_id = t.session_id
LEFT JOIN artifacts a ON s.session_id = a.session_id
LEFT JOIN session_tags st ON s.session_id = st.session_id
LEFT JOIN tags tg ON st.tag_id = tg.tag_id
GROUP BY s.session_id
ORDER BY s.start_time DESC;

-- Active sessions (not completed)
CREATE VIEW IF NOT EXISTS v_active_sessions AS
SELECT * FROM v_recent_sessions
WHERE status IN ('active', 'paused');

-- Session statistics by persona
CREATE VIEW IF NOT EXISTS v_session_stats_by_persona AS
SELECT 
    persona,
    COUNT(*) as session_count,
    AVG(resonance_score) as avg_resonance,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count,
    AVG(JULIANDAY(end_time) - JULIANDAY(start_time)) * 24 as avg_duration_hours
FROM sessions
WHERE persona IS NOT NULL
GROUP BY persona
ORDER BY session_count DESC;

-- ============================================================================
-- HELPER FUNCTIONS (stored as views for SQLite compatibility)
-- ============================================================================

-- Get session duration in minutes
CREATE VIEW IF NOT EXISTS v_session_durations AS
SELECT 
    session_id,
    title,
    start_time,
    end_time,
    CAST((JULIANDAY(COALESCE(end_time, CURRENT_TIMESTAMP)) - JULIANDAY(start_time)) * 24 * 60 AS INTEGER) as duration_minutes
FROM sessions;

-- ============================================================================
-- EXAMPLE QUERIES (for documentation)
-- ============================================================================

-- Search sessions by keyword:
--   SELECT * FROM sessions_fts WHERE sessions_fts MATCH 'BQI Phase 6';

-- Find sessions related to specific file:
--   SELECT DISTINCT s.* FROM sessions s
--   JOIN artifacts a ON s.session_id = a.session_id
--   WHERE a.file_path LIKE '%bqi_learner%';

-- Get all artifacts created in a session:
--   SELECT * FROM artifacts WHERE session_id = ?;

-- Find similar sessions (by tags):
--   SELECT s2.*, COUNT(*) as shared_tags
--   FROM session_tags st1
--   JOIN session_tags st2 ON st1.tag_id = st2.tag_id
--   JOIN sessions s2 ON st2.session_id = s2.session_id
--   WHERE st1.session_id = ? AND st2.session_id != ?
--   GROUP BY s2.session_id
--   ORDER BY shared_tags DESC;

-- Get daily activity summary:
--   SELECT DATE(start_time) as date, COUNT(*) as sessions, 
--          SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
--   FROM sessions
--   GROUP BY DATE(start_time)
--   ORDER BY date DESC;
