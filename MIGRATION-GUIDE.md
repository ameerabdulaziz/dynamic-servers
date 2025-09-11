# Database Migration Guide

## Overview

Your Dynamic Servers project now has a **Flask-Migrate** system set up to handle database schema changes. This allows you to safely apply database changes from development to your deployed servers.

## ✅ What's Been Set Up

1. **Flask-Migrate installed** and configured in `app.py`
2. **Migration repository initialized** in `migrations/` directory
3. **Initial migration created** documenting recent changes
4. **Production migration script** (`migrate_production.py`) for deployed servers

## 🔄 Migration Workflow

### Development Environment (Replit)

When you make database changes in development:

```bash
# 1. Create migration for your changes
FLASK_APP=main.py flask db migrate -m "Description of changes"

# 2. Review the generated migration file in migrations/versions/
# 3. Apply migration locally to test
FLASK_APP=main.py flask db upgrade
```

### Production/Deployed Servers

To apply changes to your deployed servers:

```bash
# 1. SSH into your deployed server
ssh user@your-server.com

# 2. Navigate to your application directory
cd /path/to/your/app

# 3. Set production database URL
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# 4. First, do a dry run to see what would change
python migrate_production.py --dry-run

# 5. Apply migrations (creates backup first)
python migrate_production.py --apply
```

## 📝 Available Migration Commands

### Development Commands (Replit)
```bash
# Initialize migrations (already done)
flask db init

# Create new migration
flask db migrate -m "Your change description"

# Apply migrations
flask db upgrade

# Show current migration status
flask db current

# Show migration history
flask db history

# Downgrade to previous migration (use with caution)
flask db downgrade
```

### Production Commands
```bash
# Safe dry-run check
python migrate_production.py --dry-run

# Apply migrations with confirmation
python migrate_production.py --apply

# Force apply without confirmation (dangerous)
python migrate_production.py --apply --force
```

## 🛡️ Safety Best Practices

### Before Any Production Migration:

1. **Backup your database**:
   ```bash
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test migrations in staging environment first**

3. **Review migration files** in `migrations/versions/` before applying

4. **Plan for rollback** - some migrations are irreversible

### During Migration:

1. **Use dry-run first** to see what will change
2. **Apply during maintenance windows** for critical systems
3. **Monitor application logs** after migration
4. **Test critical functionality** after migration

## 📁 Migration Files Structure

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py              # Migration environment setup  
├── README              # Auto-generated readme
├── script.py.mako      # Template for new migrations
└── versions/           # Individual migration files
    └── 001_remove_nova_hr_mail_server.py
```

## 🔍 Current Migrations

### Migration 001: Remove nova-hr-mail server
- **What**: Removes the deleted nova-hr-mail server and related records
- **Status**: Applied in development
- **Production**: Pending - apply with migration script

## ❗ Important Notes

1. **Environment Variables**: Production servers need `DATABASE_URL` set correctly
2. **Dependencies**: Ensure `flask-migrate` is installed on production servers
3. **Permissions**: Database user needs CREATE/ALTER permissions for migrations
4. **Downtime**: Some migrations may require brief application downtime

## 🚨 Troubleshooting

### Migration fails on production:
1. Check database permissions
2. Verify DATABASE_URL is correct  
3. Ensure no active connections blocking schema changes
4. Review migration file for syntax errors

### Database inconsistency:
1. Restore from pre-migration backup
2. Review and fix migration file
3. Re-apply corrected migration

### Need to rollback:
```bash
flask db downgrade  # Go back one migration
flask db downgrade <revision_id>  # Go back to specific migration
```

## 📞 Next Steps

1. **Apply current migration** to your production servers using the migration script
2. **Create new migrations** whenever you modify database schema in development
3. **Always test migrations** in staging before production
4. **Keep migration files** in version control for team coordination

Your database changes are now trackable, reversible, and safely deployable! 🎉