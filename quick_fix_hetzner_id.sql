-- Quick fix for hetzner_id NOT NULL constraint
-- Run this SQL command directly on your production database

ALTER TABLE hetzner_server ALTER COLUMN hetzner_id DROP NOT NULL;

-- Verify the change
\d hetzner_server