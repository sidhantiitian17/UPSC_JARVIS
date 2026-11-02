-- up
CREATE TABLE focus_sample (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('study','neutral','distraction')),
  app TEXT NOT NULL
);
CREATE INDEX idx_focus_sample_ts ON focus_sample(ts);

-- down
DROP INDEX idx_focus_sample_ts;
DROP TABLE focus_sample;
