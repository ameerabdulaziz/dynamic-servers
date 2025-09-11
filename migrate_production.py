#!/usr/bin/env python3
"""
Production Database Migration Script
====================================

This script helps apply database migrations to production/deployed servers.
Run this on your deployed servers to keep them in sync with development changes.

Usage:
    python migrate_production.py --help
    python migrate_production.py --dry-run
    python migrate_production.py --apply

Requirements:
    - Set DATABASE_URL environment variable for production database
    - Ensure Flask-Migrate is installed: pip install flask-migrate
    - Have backup of production database before running migrations
"""

import os
import sys
import argparse
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase


def setup_app():
    """Setup Flask app for migrations"""
    class Base(DeclarativeBase):
        pass
    
    app = Flask(__name__)
    db = SQLAlchemy(model_class=Base)
    migrate = Migrate()
    
    # Configure database - must set DATABASE_URL environment variable
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set!")
        print("Please set it to your production database URL")
        sys.exit(1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    return app, db, migrate


def main():
    parser = argparse.ArgumentParser(description='Apply database migrations to production')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show pending migrations without applying them')
    parser.add_argument('--apply', action='store_true',
                       help='Apply pending migrations to production database')
    parser.add_argument('--force', action='store_true',
                       help='Force apply migrations (use with caution)')
    
    args = parser.parse_args()
    
    if not (args.dry_run or args.apply):
        parser.print_help()
        return
    
    app, db, migrate = setup_app()
    
    with app.app_context():
        if args.dry_run:
            print("=== DRY RUN: Showing pending migrations ===")
            print("This will show what migrations would be applied...")
            os.system("flask db show")
            print("\nTo apply these migrations, run with --apply flag")
            
        elif args.apply:
            print("=== APPLYING MIGRATIONS TO PRODUCTION ===")
            print("WARNING: This will modify your production database!")
            
            if not args.force:
                confirm = input("Are you sure you want to proceed? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Migration cancelled.")
                    return
            
            print("Creating backup before migration...")
            backup_cmd = f"pg_dump {os.environ.get('DATABASE_URL')} > migration_backup_$(date +%Y%m%d_%H%M%S).sql"
            os.system(backup_cmd)
            
            print("Applying migrations...")
            result = os.system("flask db upgrade")
            
            if result == 0:
                print("✅ Migrations applied successfully!")
            else:
                print("❌ Migration failed! Check the error messages above.")
                print("You may need to restore from backup if database is in inconsistent state.")


if __name__ == '__main__':
    main()