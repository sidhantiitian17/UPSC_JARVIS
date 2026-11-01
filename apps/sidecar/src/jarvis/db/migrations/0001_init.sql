-- up
CREATE TABLE syllabus_node (
  id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES syllabus_node(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('paper','subject','topic','microtheme','thinker','concept')),
  paper TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0,
  target_pages INTEGER,
  reviewed INTEGER NOT NULL DEFAULT 0 CHECK (reviewed IN (0,1)),
  source TEXT NOT NULL DEFAULT 'draft'
);
CREATE INDEX idx_syllabus_parent ON syllabus_node(parent_id);

-- Generic edges of the knowledge graph (node<->chunk, node<->question, CA item<->node, ...).
CREATE TABLE link (
  src_type TEXT NOT NULL,
  src_id TEXT NOT NULL,
  dst_type TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY (src_type, src_id, dst_type, dst_id, kind)
);
CREATE INDEX idx_link_dst ON link(dst_type, dst_id);

CREATE TABLE document (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sha256 TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL,
  title TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'pdf',
  page_count INTEGER,
  scanned INTEGER NOT NULL DEFAULT 0 CHECK (scanned IN (0,1)),
  added_at TEXT NOT NULL,
  last_page INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE chunk (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  page INTEGER NOT NULL,
  ordinal INTEGER NOT NULL,
  text TEXT NOT NULL,
  char_start INTEGER NOT NULL,
  char_end INTEGER NOT NULL,
  UNIQUE (document_id, page, ordinal)
);
CREATE INDEX idx_chunk_doc_page ON chunk(document_id, page);

CREATE VIRTUAL TABLE chunk_fts USING fts5(text, content='chunk', content_rowid='id');
CREATE TRIGGER chunk_ai AFTER INSERT ON chunk BEGIN
  INSERT INTO chunk_fts(rowid, text) VALUES (new.id, new.text);
END;
CREATE TRIGGER chunk_ad AFTER DELETE ON chunk BEGIN
  INSERT INTO chunk_fts(chunk_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
CREATE TRIGGER chunk_au AFTER UPDATE ON chunk BEGIN
  INSERT INTO chunk_fts(chunk_fts, rowid, text) VALUES ('delete', old.id, old.text);
  INSERT INTO chunk_fts(rowid, text) VALUES (new.id, new.text);
END;

CREATE TABLE study_session (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL REFERENCES document(id) ON DELETE CASCADE,
  start_chunk_id INTEGER REFERENCES chunk(id) ON DELETE SET NULL,
  end_chunk_id INTEGER REFERENCES chunk(id) ON DELETE SET NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  focused_seconds INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','gate','done','skipped'))
);

CREATE TABLE question (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL CHECK (kind IN ('mcq','mains','dq')),
  source TEXT NOT NULL CHECK (source IN ('pyq','generated','fallback')),
  stem TEXT NOT NULL,
  options_json TEXT,
  answer_index INTEGER,
  explanation TEXT,
  source_chunk_id INTEGER REFERENCES chunk(id) ON DELETE SET NULL,
  source_quote TEXT,
  pyq_id TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','reported','retired')),
  created_at TEXT NOT NULL
);

CREATE TABLE attempt (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
  session_id INTEGER REFERENCES study_session(id) ON DELETE SET NULL,
  chosen_index INTEGER,
  correct INTEGER NOT NULL CHECK (correct IN (0,1)),
  confidence TEXT CHECK (confidence IN ('G','A','R')),
  time_ms INTEGER,
  mistake_type TEXT CHECK (mistake_type IN ('conceptual','revision','silly','over_elimination')),
  answered_at TEXT NOT NULL
);
CREATE INDEX idx_attempt_question ON attempt(question_id);

CREATE TABLE card (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL UNIQUE REFERENCES question(id) ON DELETE CASCADE,
  due TEXT NOT NULL,
  state_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  suspended INTEGER NOT NULL DEFAULT 0 CHECK (suspended IN (0,1))
);
CREATE INDEX idx_card_due ON card(due);

CREATE TABLE review_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id INTEGER NOT NULL REFERENCES card(id) ON DELETE CASCADE,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 4),
  reviewed_at TEXT NOT NULL,
  scheduled_days REAL,
  state_before_json TEXT
);

CREATE TABLE llm_cache (
  key TEXT PRIMARY KEY,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  hits INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE llm_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  task TEXT NOT NULL,
  tokens_in INTEGER,
  tokens_out INTEGER,
  status TEXT NOT NULL,
  cache_hit INTEGER NOT NULL DEFAULT 0 CHECK (cache_hit IN (0,1))
);
CREATE INDEX idx_llm_usage_ts ON llm_usage(ts);

CREATE TABLE setting (
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL
);

-- down
DROP TABLE setting;
DROP INDEX idx_llm_usage_ts;
DROP TABLE llm_usage;
DROP TABLE llm_cache;
DROP TABLE review_log;
DROP INDEX idx_card_due;
DROP TABLE card;
DROP INDEX idx_attempt_question;
DROP TABLE attempt;
DROP TABLE question;
DROP TABLE study_session;
DROP TRIGGER chunk_au;
DROP TRIGGER chunk_ad;
DROP TRIGGER chunk_ai;
DROP TABLE chunk_fts;
DROP INDEX idx_chunk_doc_page;
DROP TABLE chunk;
DROP TABLE document;
DROP INDEX idx_link_dst;
DROP TABLE link;
DROP INDEX idx_syllabus_parent;
DROP TABLE syllabus_node;
