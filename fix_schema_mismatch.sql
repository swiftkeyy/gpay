-- CRITICAL FIX: Schema mismatch between migration and models
-- This script fixes the immediate issues to get the bot running
-- Run this in Railway PostgreSQL Query tab

-- Step 1: Drop all tables to start fresh
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Step 2: Mark migration as not applied
-- (This will be recreated when you redeploy)
