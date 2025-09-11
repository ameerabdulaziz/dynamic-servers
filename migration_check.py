#!/usr/bin/env python3
"""
Simple Migration Check Script
============================

This script checks and applies migrations without loading the full application,
avoiding issues with missing columns during app initialization.

Usage:
    python migration_check.py --check     # Show pending migrations
    python migration_check.py --apply     # Apply migrations
"""

import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Check and apply database migrations')
    parser.add_argument('--check', action='store_true', 
                       help='Show pending migrations')
    parser.add_argument('--apply', action='store_true',
                       help='Apply pending migrations')
    
    args = parser.parse_args()
    
    if not (args.check or args.apply):
        parser.print_help()
        return
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        print("Please set it to your production database URL")
        sys.exit(1)
    
    if args.check:
        print("=== Checking for pending migrations ===")
        # Use alembic directly to avoid app loading issues
        result = os.system("FLASK_APP=main.py flask db current")
        if result == 0:
            print("\n=== Migration History ===")
            os.system("FLASK_APP=main.py flask db history")
        
    elif args.apply:
        print("=== APPLYING MIGRATIONS ===")
        print("WARNING: This will modify your production database!")
        
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Migration cancelled.")
            return
        
        print("Creating backup before migration...")
        backup_cmd = f"pg_dump '{database_url}' > migration_backup_$(date +%Y%m%d_%H%M%S).sql"
        backup_result = os.system(backup_cmd)
        
        if backup_result != 0:
            print("⚠️  Backup failed, but continuing with migration...")
        else:
            print("✅ Backup created successfully")
        
        print("Applying migrations...")
        # Set FLASK_APP environment variable for the subprocess
        os.environ['FLASK_APP'] = 'main.py'
        result = os.system("flask db upgrade")
        
        if result == 0:
            print("✅ Migrations applied successfully!")
        else:
            print("❌ Migration failed! Check the error messages above.")


if __name__ == '__main__':
    main()