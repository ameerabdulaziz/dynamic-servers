-- Fix image column to be nullable for self-hosted servers
ALTER TABLE hetzner_server ALTER COLUMN image DROP NOT NULL;