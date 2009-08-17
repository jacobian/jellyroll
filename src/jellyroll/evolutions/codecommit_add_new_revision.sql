ALTER TABLE jellyroll_codecommit ADD COLUMN new_revision VARCHAR(200) DEFAULT '';
UPDATE jellyroll_codecommit SET new_revision = revision::text;