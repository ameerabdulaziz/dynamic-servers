#!/bin/bash

# Complete restore script for Docker PostgreSQL
# This script will safely restore the Dynamic Servers database

set -e  # Exit on any error

echo "🔄 Starting Docker database restore..."

# Configuration
POSTGRES_USER="dynamic_user"
DATABASE_NAME="dynamic_servers" 
SCHEMA_FILE="schema_only_backup_20250902_202247.sql"
DATA_FILE="data_only_backup_20250902_202233.sql"

# Check if files exist
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ Schema file not found: $SCHEMA_FILE"
    exit 1
fi

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Data file not found: $DATA_FILE"
    exit 1
fi

# Check if Docker containers are running
if ! docker compose ps | grep -q "postgres"; then
    echo "❌ PostgreSQL container not running. Start with: docker compose up -d"
    exit 1
fi

echo "📋 Files ready:"
echo "   Schema: $SCHEMA_FILE ($(ls -lh $SCHEMA_FILE | awk '{print $5}'))"
echo "   Data: $DATA_FILE ($(ls -lh $DATA_FILE | awk '{print $5}'))"

read -p "⚠️  This will DELETE all existing data in '$DATABASE_NAME'. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

echo "🗑️  Dropping existing database..."
docker compose exec postgres psql -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS $DATABASE_NAME;"

echo "🏗️  Creating fresh database..."
docker compose exec postgres psql -U $POSTGRES_USER -c "CREATE DATABASE $DATABASE_NAME;"
docker compose exec postgres psql -U $POSTGRES_USER -c "GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $POSTGRES_USER;"

echo "📊 Restoring database schema..."
if docker compose exec -T postgres psql -U $POSTGRES_USER -d $DATABASE_NAME < $SCHEMA_FILE; then
    echo "✅ Schema restored successfully"
else
    echo "❌ Schema restore failed"
    exit 1
fi

echo "📦 Restoring database data..."
if docker compose exec -T postgres psql -U $POSTGRES_USER -d $DATABASE_NAME < $DATA_FILE; then
    echo "✅ Data restored successfully"
else
    echo "⚠️  Data restore had issues - checking..."
    
    # Check if basic tables exist and have data
    echo "🔍 Verifying restore..."
    user_count=$(docker compose exec postgres psql -U $POSTGRES_USER -d $DATABASE_NAME -t -c "SELECT COUNT(*) FROM \"user\";" 2>/dev/null | xargs || echo "0")
    project_count=$(docker compose exec postgres psql -U $POSTGRES_USER -d $DATABASE_NAME -t -c "SELECT COUNT(*) FROM hetzner_projects;" 2>/dev/null | xargs || echo "0")
    
    if [ "$user_count" -gt "0" ] && [ "$project_count" -gt "0" ]; then
        echo "✅ Core data restored ($user_count users, $project_count projects)"
    else
        echo "❌ Data restore verification failed"
        exit 1
    fi
fi

echo "🔍 Verifying final database state..."
docker compose exec postgres psql -U $POSTGRES_USER -d $DATABASE_NAME -c "
    SELECT 
        'Users: ' || COUNT(*) as info FROM \"user\"
    UNION ALL
    SELECT 
        'Projects: ' || COUNT(*) as info FROM hetzner_projects  
    UNION ALL
    SELECT 
        'Servers: ' || COUNT(*) as info FROM hetzner_server
    UNION ALL  
    SELECT 
        'Requests: ' || COUNT(*) as info FROM server_request;
"

echo ""
echo "🎉 Database restore completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Update your .env file with database connection"
echo "   2. Add your API keys (HETZNER_API_TOKEN, GODADDY_API_KEY, etc.)"
echo "   3. Start your application: docker compose up -d"
echo "   4. Test login with existing users"
echo ""
echo "🔐 Remember to update API tokens and secrets for your environment!"