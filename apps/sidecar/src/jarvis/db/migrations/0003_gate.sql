-- up
CREATE TABLE gate_question (
  session_id INTEGER NOT NULL REFERENCES study_session(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  interleaved INTEGER NOT NULL DEFAULT 0 CHECK (interleaved IN (0,1)),
  PRIMARY KEY (session_id, question_id)
);
CREATE TABLE question_report (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question_id INTEGER NOT NULL REFERENCES question(id) ON DELETE CASCADE,
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
ALTER TABLE question ADD COLUMN style TEXT NOT NULL DEFAULT 'recall' CHECK (style IN ('recall','application'));

-- down
ALTER TABLE question DROP COLUMN style;
DROP TABLE question_report;
DROP TABLE gate_question;
