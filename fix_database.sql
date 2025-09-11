-- Fix database transaction state and add missing columns
-- Run these commands directly in your PostgreSQL database

-- 1. First, end any open transactions
ROLLBACK;

-- 2. Add missing columns if they don't exist
ALTER TABLE hetzner_server ADD COLUMN IF NOT EXISTS server_source VARCHAR(20) DEFAULT 'hetzner' NOT NULL;
ALTER TABLE hetzner_server ADD COLUMN IF NOT EXISTS client_name VARCHAR(100);
ALTER TABLE hetzner_server ADD COLUMN IF NOT EXISTS client_contact VARCHAR(255);

-- 3. Make hetzner_id nullable for self-hosted servers
ALTER TABLE hetzner_server ALTER COLUMN hetzner_id DROP NOT NULL;

-- 4. Update the migration version table to mark migrations as applied
-- (Only run these if the alembic_version table exists)
UPDATE alembic_version SET version_num='002' WHERE version_num='001';
INSERT INTO alembic_version (version_num) VALUES ('003') ON CONFLICT DO NOTHING;

-- 5. Verify the changes
\d hetzner_server