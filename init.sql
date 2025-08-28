-- Database initialization script
-- This runs when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
-- Note: Tables will be created by SQLAlchemy, this is just for additional setup

-- Set timezone
SET timezone = 'UTC';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE dynamic_servers TO dynamic_user;