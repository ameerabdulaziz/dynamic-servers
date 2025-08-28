# Database Backup and Restore Guide

## Current Backup Files Available

You now have downloadable PostgreSQL backup files ready for your Docker deployment:

### Available Backups
- `dynamic_servers_backup_20250828_170049.sql` (58.6 KB) - Latest backup
- Available at: `/static/backups/` directory
- Download via web interface: Admin Dashboard → View Backups

## How to Use These Backups in Your Docker Environment

### Method 1: Direct Restore (Recommended)

1. **Download the backup file** from the admin panel or directly:
   ```bash
   # Download via web interface or copy the file
   wget http://your-server:5000/static/backups/dynamic_servers_backup_20250828_170049.sql
   ```

2. **Stop your current Docker services:**
   ```bash
   docker-compose down
   ```

3. **Remove old database volume (if starting fresh):**
   ```bash
   docker volume rm dynamic-servers_postgres_data
   ```

4. **Start database service only:**
   ```bash
   docker-compose up -d db
   sleep 10  # Wait for database to initialize
   ```

5. **Restore the backup:**
   ```bash
   cat dynamic_servers_backup_20250828_170049.sql | docker-compose exec -T db psql -U dynamic_user -d dynamic_servers
   ```

6. **Start web service:**
   ```bash
   docker-compose up -d web
   ```

### Method 2: Copy and Restore Inside Container

1. **Start Docker services:**
   ```bash
   docker-compose up -d
   ```

2. **Copy backup file to container:**
   ```bash
   docker cp dynamic_servers_backup_20250828_170049.sql dynamic-servers_db_1:/tmp/
   ```

3. **Restore inside container:**
   ```bash
   docker-compose exec db psql -U dynamic_user -d dynamic_servers -f /tmp/dynamic_servers_backup_20250828_170049.sql
   ```

### Method 3: Volume Mounting (Development)

Add to your `docker-compose.override.yml`:

```yaml
services:
  db:
    volumes:
      - ./backups:/backups:ro
```

Then restore:
```bash
docker-compose exec db psql -U dynamic_user -d dynamic_servers -f /backups/dynamic_servers_backup_20250828_170049.sql
```

## Backup Contents

The backup includes:
- ✅ All user accounts and roles
- ✅ Server requests and approvals
- ✅ Hetzner server configurations
- ✅ Project access permissions
- ✅ Deployment scripts and execution logs
- ✅ Client subscriptions and billing data
- ✅ Database backup records
- ✅ System update history
- ✅ Notification history

## Verification After Restore

1. **Check if services start properly:**
   ```bash
   docker-compose logs web
   docker-compose logs db
   ```

2. **Test database connectivity:**
   ```bash
   docker-compose exec db psql -U dynamic_user -d dynamic_servers -c "SELECT COUNT(*) FROM users;"
   ```

3. **Access web interface:**
   - Open http://localhost:5000
   - Login with existing admin credentials
   - Verify all data is present

## Automated Backup Creation

The system now includes automated backup functionality:

### Via Web Interface:
- Admin Dashboard → "Create Backup" button
- Admin Dashboard → "View Backups" to see all available backups
- Each backup is automatically timestamped and downloadable

### Via Command Line:
```bash
python create_backup.py create  # Create new backup
python create_backup.py list    # List all backups
python create_backup.py cleanup # Clean up old backups
```

## Backup File Details

- **Format:** PostgreSQL SQL dump
- **Options:** `--no-owner --no-privileges` (for easier restoration)
- **Naming:** `dynamic_servers_backup_YYYYMMDD_HHMMSS.sql`
- **Location:** `static/backups/` directory
- **Cleanup:** Automatically keeps 5 most recent backups

## Production Deployment Notes

1. **Environment Variables:** Make sure to set proper values in `.env`:
   ```bash
   SESSION_SECRET=your-secure-session-secret
   HETZNER_API_TOKEN=your-hetzner-api-token
   DATABASE_URL=postgresql://dynamic_user:dynamic_pass@db:5432/dynamic_servers
   ```

2. **SSH Keys:** Mount your SSH keys for server management:
   ```bash
   # Ensure SSH keys exist and have correct permissions
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/*
   ```

3. **Volumes:** Database data persists in `postgres_data` volume
4. **Networking:** Services communicate via `dynamic-servers` network
5. **Health Checks:** Built-in health monitoring for both services

## Troubleshooting

### Common Issues:

1. **Permission errors:**
   ```bash
   sudo chown -R 999:999 postgres_data/  # PostgreSQL user in container
   ```

2. **Database connection refused:**
   ```bash
   docker-compose logs db  # Check database logs
   ```

3. **Restore fails with "database does not exist":**
   ```bash
   docker-compose exec db createdb -U dynamic_user dynamic_servers
   ```

4. **Web service fails to start:**
   ```bash
   docker-compose logs web  # Check application logs
   ```

## Security Considerations

- Backup files contain sensitive data (user passwords, API tokens)
- Store backups securely and encrypt if necessary
- Regular backup rotation and cleanup
- Access restricted to admin users only
- Use strong database passwords in production

Your Dynamic Servers system is now fully containerized with comprehensive backup and restore capabilities!