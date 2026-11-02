-- up
CREATE TABLE pyq (
  id TEXT PRIMARY KEY,
  phase TEXT NOT NULL CHECK (phase IN ('prelims','mains','optional')),
  year INTEGER NOT NULL,
  paper TEXT NOT NULL,
  number INTEGER NOT NULL,
  page INTEGER,
  marks REAL,
  negative_marks REAL,
  stem TEXT NOT NULL DEFAULT '',
  options_json TEXT NOT NULL DEFAULT '[]',
  raw_text TEXT,
  answer TEXT CHECK (answer IS NULL OR answer IN ('a','b','c','d')),
  answer_source TEXT NOT NULL DEFAULT 'none' CHECK (answer_source IN ('official-key','owner-verified','none')),
  suggested_answer TEXT,
  status TEXT NOT NULL DEFAULT 'parsed' CHECK (status IN ('parsed','reviewed','verified','failed')),
  source_url TEXT,
  source_sha256 TEXT,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_pyq_paper ON pyq(phase, year, paper);
CREATE INDEX idx_pyq_status ON pyq(status);

-- down
DROP INDEX idx_pyq_status;
DROP INDEX idx_pyq_paper;
DROP TABLE pyq;
