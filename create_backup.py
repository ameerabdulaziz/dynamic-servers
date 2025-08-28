#!/usr/bin/env python3
"""
Database Backup Script for Dynamic Servers
Creates downloadable PostgreSQL backups
"""

import os
import subprocess
import datetime
from pathlib import Path

def create_database_backup():
    """Create a PostgreSQL backup and save it to static/backups"""
    
    # Ensure backups directory exists
    backup_dir = Path("static/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"dynamic_servers_backup_{timestamp}.sql"
    backup_path = backup_dir / backup_filename
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    try:
        # Create the backup using pg_dump
        print(f"Creating database backup: {backup_filename}")
        
        with open(backup_path, 'w') as backup_file:
            subprocess.run([
                'pg_dump', 
                database_url,
                '--verbose',
                '--no-owner',
                '--no-privileges'
            ], stdout=backup_file, check=True)
        
        # Get file size for confirmation
        file_size = backup_path.stat().st_size
        print(f"Backup created successfully!")
        print(f"File: {backup_path}")
        print(f"Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Create a latest symlink for convenience
        latest_backup = backup_dir / "latest_backup.sql"
        if latest_backup.exists():
            latest_backup.unlink()
        latest_backup.symlink_to(backup_filename)
        
        return backup_filename
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create backup - {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error - {e}")
        return False

def list_backups():
    """List all available backups"""
    backup_dir = Path("static/backups")
    if not backup_dir.exists():
        print("No backups directory found")
        return []
    
    backups = list(backup_dir.glob("dynamic_servers_backup_*.sql"))
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print("\nAvailable backups:")
    for backup in backups:
        stat = backup.stat()
        size = stat.st_size
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
        print(f"  {backup.name} - {size:,} bytes - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return [b.name for b in backups]

def cleanup_old_backups(keep_count=5):
    """Keep only the most recent N backups"""
    backup_dir = Path("static/backups")
    if not backup_dir.exists():
        return
    
    backups = list(backup_dir.glob("dynamic_servers_backup_*.sql"))
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if len(backups) > keep_count:
        print(f"\nCleaning up old backups (keeping {keep_count} most recent):")
        for old_backup in backups[keep_count:]:
            print(f"  Removing: {old_backup.name}")
            old_backup.unlink()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "create":
            result = create_database_backup()
            if result:
                print(f"\n✅ Backup created: {result}")
                print(f"📁 Download URL: /static/backups/{result}")
            cleanup_old_backups()
            
        elif command == "list":
            list_backups()
            
        elif command == "cleanup":
            keep = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            cleanup_old_backups(keep)
            
        else:
            print("Usage: python create_backup.py [create|list|cleanup]")
    else:
        # Default: create backup
        result = create_database_backup()
        if result:
            print(f"\n✅ Backup created: {result}")
            print(f"📁 Download URL: /static/backups/{result}")
        cleanup_old_backups()