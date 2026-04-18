-- Mark the migration as already applied
-- Run this in Railway PostgreSQL Query tab

INSERT INTO alembic_version (version_num) 
VALUES ('20260418_000001')
ON CONFLICT (version_num) DO NOTHING;

-- Verify it was inserted
SELECT * FROM alembic_version;
