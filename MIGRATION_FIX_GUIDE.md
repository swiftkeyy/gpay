# Migration Schema Mismatch Fix

## Problem
The migration file `20260418_000001_initial_schema.py` has an outdated schema that doesn't match the current models in `app/models/entities.py`.

**Key mismatches:**
- `games` table: migration has `name`, `display_name`, `icon_url` but model expects `slug`, `title`, `description`, `image_id`
- `products` table: migration has old schema without `category_id`, `slug`, etc.
- `categories` table: completely missing from migration
- Many other tables missing: `prices`, `promo_codes`, `bot_settings`, `broadcasts`, `audit_logs`, `user_blocks`, `referrals`, `referral_rewards`, `reviews`, `order_status_history`

## Solution: Regenerate Migration from Models

### Step 1: Delete the old migration file
```bash
cd ПРОЕКТЫ/gpay-main
rm alembic/versions/20260418_000001_initial_schema.py
rm alembic/versions/20260418_154000_add_bot_settings.py
```

### Step 2: Generate new migration from current models
```bash
alembic revision --autogenerate -m "initial_schema_complete"
```

This will create a new migration file that matches your current models exactly.

### Step 3: Review the generated migration
Open the new migration file in `alembic/versions/` and verify it includes all tables from your models.

### Step 4: Drop and recreate database in Railway

In Railway PostgreSQL Query tab, run:
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

### Step 5: Redeploy in Railway
Click "Redeploy" in Railway. The new migration will run and create all tables correctly.

## Alternative: Quick Manual Fix (if autogenerate doesn't work)

If you can't run `alembic revision --autogenerate` locally, I can manually create the complete migration file for you. Just let me know and I'll generate it based on your current models.

## Why This Happened
The migration file was created from an older version of the models. When you modernized the app and changed the schema (added categories, changed games structure, etc.), the migration wasn't updated to match.
