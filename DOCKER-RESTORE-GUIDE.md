# Docker Database Restore Guide

## Issue Analysis
Your restore failed because you're trying to restore into an existing database with existing tables and data. This causes conflicts with:
- Duplicate tables
- Foreign key constraint violations  
- Missing user references
- Ownership conflicts

## Solution: Clean Restore Process

### Step 1: Drop and Recreate Database
```bash
# Connect to your Docker PostgreSQL container
docker compose exec postgres psql -U dynamic_user

# Drop the existing database (this will remove ALL data)
DROP DATABASE IF EXISTS dynamic_servers;

# Recreate the database
CREATE DATABASE dynamic_servers;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dynamic_servers TO dynamic_user;

# Exit
\q
```

### Step 2: Restore Schema First
```bash
# Restore the schema (tables structure only)
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < schema_only_backup_20250902_202247.sql
```

### Step 3: Restore Data Second
```bash
# Restore the data
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < data_only_backup_20250902_202233.sql
```

## Alternative: Use INSERT Statements

If you still have issues, here's a manual approach:

### Step 1: Clean Database Setup
```sql
-- Connect to database
docker compose exec postgres psql -U dynamic_user -d dynamic_servers

-- Drop all tables (careful!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO dynamic_user;
```

### Step 2: Create Tables Manually
Use the schema backup to create tables without conflicts.

### Step 3: Insert Data in Order
Insert data in the correct order to avoid foreign key violations:
1. Users first (no dependencies)
2. Hetzner projects  
3. Servers
4. Everything else

## Quick Fix for Your Current Situation

Since you have existing data, let's sync only the missing data:

```bash
# Export only new/missing records from source
pg_dump $SOURCE_DATABASE --data-only --table=user --table=hetzner_projects > essential_data.sql

# Import to your database
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < essential_data.sql
```

## Environment Variables for Docker

Make sure your Docker environment has:

```yaml
# In your docker-compose.yml or .env file
DATABASE_URL=postgresql://dynamic_user:your_password@postgres:5432/dynamic_servers
SESSION_SECRET=your-session-secret-here
HETZNER_API_TOKEN=your-hetzner-token
GODADDY_API_KEY=your-godaddy-key
GODADDY_API_SECRET=your-godaddy-secret
```

## Prevention

To avoid this in future:
1. Always backup to a fresh, empty database
2. Use `--clean --if-exists` flags for pg_dump
3. Test restore process on a separate database first

Your restore failed because of existing data conflicts. Follow the clean database approach above for a successful restore!