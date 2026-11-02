-- up
CREATE TABLE gate_result (
  session_id INTEGER PRIMARY KEY REFERENCES study_session(id) ON DELETE CASCADE,
  total INTEGER NOT NULL,
  correct INTEGER NOT NULL,
  retention_pct INTEGER NOT NULL,
  passed INTEGER NOT NULL CHECK (passed IN (0,1)),
  skipped INTEGER NOT NULL DEFAULT 0 CHECK (skipped IN (0,1)),
  xp INTEGER NOT NULL DEFAULT 0,
  finished_at TEXT NOT NULL
);

-- down
DROP TABLE gate_result;
