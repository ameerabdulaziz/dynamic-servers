# Database Backup and Restore Instructions

## Backup Information
- **Backup File**: `database_backup_20250902_201556.sql`
- **Backup Date**: September 2, 2025
- **Database Size**: ~63KB
- **Format**: PostgreSQL SQL dump

## What's Included in the Backup

This backup contains the complete Dynamic Servers database with:

### Tables and Data:
- **Users**: All user accounts (admin, sales agents, technical agents)
- **Server Requests**: Complete history of server provisioning requests
- **Hetzner Projects**: All configured projects with API tokens and base domains
- **Hetzner Servers**: All managed servers with connection details
- **Project Access**: User permission assignments for projects
- **Server Assignments**: Technical agent assignments to specific servers
- **Deployment Scripts**: All Ansible playbooks and custom scripts
- **Deployment Executions**: History of script executions and results
- **Notifications**: System notifications and alerts
- **Subscriptions**: Client hosting subscriptions and billing info
- **Database Backups**: Backup history records
- **System Updates**: Update history and logs

### Key Configuration:
- Nova HR project: novahrs.com domain
- Frappe ERP project: erp.dynamicservers.io domain
- Django Projects: django.dynamicservers.io domain
- Complete user access control setup
- Server provisioning automation configuration

## Restore Instructions

### Prerequisites
1. PostgreSQL server running on your target system
2. `psql` command line tool installed
3. Database user with CREATE privileges

### Step 1: Create Database
```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create database
CREATE DATABASE dynamic_servers;

# Create user (optional)
CREATE USER dynamic_servers_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dynamic_servers TO dynamic_servers_user;

# Exit PostgreSQL
\q
```

### Step 2: Restore from Backup
```bash
# Restore the database (replace with your connection details)
psql -h localhost -U dynamic_servers_user -d dynamic_servers < database_backup_20250902_201556.sql

# OR if using default PostgreSQL user
sudo -u postgres psql dynamic_servers < database_backup_20250902_201556.sql
```

### Step 3: Verify Restore
```sql
-- Connect to the database
psql -h localhost -U dynamic_servers_user -d dynamic_servers

-- Check tables exist
\dt

-- Verify data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM server_request;
SELECT COUNT(*) FROM hetzner_project;

-- Exit
\q
```

## Environment Variables for Your Server

After restoring, configure these environment variables:

```bash
# Database connection
DATABASE_URL="postgresql://dynamic_servers_user:your_password@localhost:5432/dynamic_servers"

# Required secrets (you'll need to obtain these)
SESSION_SECRET="your-session-secret-key"
HETZNER_API_TOKEN="your-hetzner-token"
GODADDY_API_KEY="your-godaddy-api-key"  
GODADDY_API_SECRET="your-godaddy-api-secret"

# Optional - for different projects
NOVA_HR_HETZNER_TOKEN="project-specific-token"
FRAPPE_ERP_HETZNER_TOKEN="project-specific-token"
DJANGO_PROJECTS_HETZNER_TOKEN="project-specific-token"
```

## Post-Restore Configuration

1. **Update API Tokens**: Replace Hetzner and GoDaddy tokens with your own
2. **Update Base Domains**: Modify project base domains if needed
3. **Test Connections**: Verify Hetzner Cloud and GoDaddy API connectivity
4. **Update SSH Keys**: Configure SSH keys for server management
5. **Test User Login**: Verify user authentication works

## Security Notes

⚠️ **Important Security Reminders:**
- Change all default passwords after restore
- Update API tokens and secrets
- Review user access permissions
- Enable SSL/TLS for production deployment
- Configure proper firewall rules
- Set up regular backup schedule

## Support

If you encounter issues during restore:
1. Check PostgreSQL logs: `/var/log/postgresql/`
2. Verify database user permissions
3. Ensure PostgreSQL version compatibility (9.5+)
4. Check disk space availability

The backup includes all automation features for server provisioning and DNS management!