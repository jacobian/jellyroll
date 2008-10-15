ALTER TABLE jellyroll_codecommit DROP COLUMN revision;
ALTER TABLE jellyroll_codecommit RENAME COLUMN new_revision TO revision;
ALTER TABLE jellyroll_codecommit ALTER COLUMN revision DROP DEFAULT;