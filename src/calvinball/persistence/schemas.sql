CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    depth TEXT NOT NULL DEFAULT 'normal',
    threads TEXT DEFAULT '[]',       -- JSON array
    findings TEXT DEFAULT '[]',      -- JSON array
    messages TEXT DEFAULT '[]',      -- JSON array (full LLM message history)
    report TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS integrations (
    name TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    config TEXT DEFAULT '{}',         -- JSON
    module_path TEXT,                 -- path to .py file for generated integrations
    is_generated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    source TEXT,                      -- investigation id or 'user'
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT,
    tool_name TEXT NOT NULL,
    input TEXT,                       -- JSON
    output TEXT,                      -- JSON
    duration_ms REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id)
);
