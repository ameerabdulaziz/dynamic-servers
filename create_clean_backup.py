#!/usr/bin/env python3
"""
Create a clean database backup that can be restored to a fresh database
without conflicts or missing foreign key references.
"""

import os
import subprocess
import sys
from datetime import datetime

def create_clean_backup():
    """Create a clean database backup with proper data ordering"""
    
    # Get database connection details
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"clean_backup_{timestamp}.sql"
    
    print(f"Creating clean backup: {backup_filename}")
    
    # Create backup with specific options for clean restore
    cmd = [
        'pg_dump',
        database_url,
        '--clean',           # Include DROP commands
        '--if-exists',       # Use IF EXISTS for DROP commands
        '--no-owner',        # Don't include ownership commands
        '--no-privileges',   # Don't include privilege commands
        '--data-only',       # Only include data, not schema
        '--file', backup_filename
    ]
    
    try:
        # First create schema-only backup
        schema_filename = f"schema_only_{timestamp}.sql"
        schema_cmd = [
            'pg_dump',
            database_url,
            '--schema-only',
            '--no-owner',
            '--no-privileges',
            '--file', schema_filename
        ]
        
        print("Creating schema backup...")
        subprocess.run(schema_cmd, check=True)
        
        # Then create data-only backup
        print("Creating data backup...")
        subprocess.run(cmd, check=True)
        
        # Create combined clean backup
        combined_filename = f"complete_clean_backup_{timestamp}.sql"
        
        print("Creating combined backup...")
        with open(combined_filename, 'w') as outfile:
            # Write schema first
            with open(schema_filename, 'r') as schema_file:
                outfile.write("-- Schema Definition\n")
                outfile.write("-- Generated: " + datetime.now().isoformat() + "\n\n")
                outfile.write(schema_file.read())
                outfile.write("\n\n")
            
            # Write data second
            with open(data_filename, 'r') as data_file:
                outfile.write("-- Data Insert\n")
                outfile.write(data_file.read())
        
        # Clean up intermediate files
        os.remove(schema_filename)
        
        print(f"✅ Clean backup created: {combined_filename}")
        print(f"✅ Data backup created: {backup_filename}")
        
        # Show file sizes
        schema_size = os.path.getsize(combined_filename)
        data_size = os.path.getsize(backup_filename)
        
        print(f"Schema + Data backup: {schema_size:,} bytes")
        print(f"Data only backup: {data_size:,} bytes")
        
        return combined_filename, backup_filename
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Backup failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_clean_backup()