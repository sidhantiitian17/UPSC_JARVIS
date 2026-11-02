-- up
CREATE TABLE pyq_tag (
  pyq_id TEXT NOT NULL REFERENCES pyq(id) ON DELETE CASCADE,
  node_id TEXT NOT NULL REFERENCES syllabus_node(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('suggested','accepted','rejected')),
  source TEXT NOT NULL CHECK (source IN ('llm','keyword','owner')),
  created_at TEXT NOT NULL,
  PRIMARY KEY (pyq_id, node_id)
);
CREATE INDEX idx_pyq_tag_node ON pyq_tag(node_id, status);

-- down
DROP INDEX idx_pyq_tag_node;
DROP TABLE pyq_tag;
