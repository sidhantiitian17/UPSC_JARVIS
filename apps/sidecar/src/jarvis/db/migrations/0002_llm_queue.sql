-- up
CREATE TABLE llm_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task TEXT NOT NULL,
  request_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','done','failed'))
);
CREATE INDEX idx_llm_queue_status ON llm_queue(status);

-- down
DROP INDEX idx_llm_queue_status;
DROP TABLE llm_queue;
