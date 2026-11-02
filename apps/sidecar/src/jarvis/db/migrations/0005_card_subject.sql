-- up
ALTER TABLE card ADD COLUMN subject_id TEXT;

-- down
ALTER TABLE card DROP COLUMN subject_id;
