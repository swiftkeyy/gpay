-- Reset Alembic version table
-- Run this in Railway PostgreSQL Query tab

-- Delete the old migration reference
DELETE FROM alembic_version;

-- The database will be empty and ready for the new migration
