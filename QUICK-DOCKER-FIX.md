# Quick Docker Database Restore Fix

## The Problem
PostgreSQL requires connecting to an existing database to create/drop other databases. You can't connect directly to a user database that doesn't exist yet.

## Quick Solution

### Step 1: Connect as PostgreSQL superuser to create database
```bash
# Connect as postgres superuser (not dynamic_user)
docker compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS dynamic_servers;"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE dynamic_servers;"
docker compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE dynamic_servers TO dynamic_user;"
```

### Step 2: Now restore as dynamic_user
```bash
# Restore schema
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < schema_only_backup_20250902_202247.sql

# Restore data  
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < data_only_backup_20250902_202233.sql
```

### Step 3: Verify restore
```bash
# Check data
docker compose exec postgres psql -U dynamic_user -d dynamic_servers -c "SELECT COUNT(*) FROM \"user\";"
docker compose exec postgres psql -U dynamic_user -d dynamic_servers -c "SELECT COUNT(*) FROM hetzner_projects;"
```

## Alternative: Connect to Default Database First
```bash
# Connect to default 'postgres' database to manage others
docker compose exec postgres psql -U dynamic_user -d postgres -c "DROP DATABASE IF EXISTS dynamic_servers;"
docker compose exec postgres psql -U dynamic_user -d postgres -c "CREATE DATABASE dynamic_servers;"
```

## Your Docker Compose Setup
Make sure your `docker-compose.yml` has:
```yaml
services:
  postgres:  # Note: service name (not 'postgress')
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_postgres_password
      POSTGRES_DB: postgres
    # Also create your dynamic_user
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

And in `init.sql`:
```sql
CREATE USER dynamic_user WITH PASSWORD 'your_password';
CREATE DATABASE dynamic_servers OWNER dynamic_user;
GRANT ALL PRIVILEGES ON DATABASE dynamic_servers TO dynamic_user;
```

## Fixed Commands
```bash
# Use 'postgres' service name (not 'postgress')
docker compose exec postgres psql -U postgres -c "CREATE DATABASE dynamic_servers;"

# Then restore
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < schema_only_backup_20250902_202247.sql
docker compose exec -T postgres psql -U dynamic_user -d dynamic_servers < data_only_backup_20250902_202233.sql
```

The key is connecting as the PostgreSQL superuser first to manage databases, then switching to your application user for data operations.