# Docker Deployment Guide

## Quick Start

### Production Deployment

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dynamic-servers
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Build and run:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Web interface: http://localhost:5000
   - Database: postgresql://dynamic_user:dynamic_pass@localhost:5432/dynamic_servers

### Development Setup

1. **Run with development overrides:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up
   ```

2. **This enables:**
   - Live code reloading
   - Debug mode
   - Source code mounting
   - Development database

## Docker Commands

### Basic Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f web

# Restart web service
docker-compose restart web

# Rebuild after code changes
docker-compose build web
docker-compose up -d web
```

### Database Operations

```bash
# Access database directly
docker-compose exec db psql -U dynamic_user -d dynamic_servers

# Create database backup
docker-compose exec db pg_dump -U dynamic_user dynamic_servers > backup.sql

# Restore database backup
docker-compose exec -T db psql -U dynamic_user -d dynamic_servers < backup.sql

# View database logs
docker-compose logs -f db
```

### Maintenance

```bash
# Clean up unused images and containers
docker system prune

# Update to latest images
docker-compose pull
docker-compose up -d

# View resource usage
docker stats
```

## Environment Variables

Required environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Flask session secret key
- `HETZNER_API_TOKEN`: Hetzner Cloud API token

Optional environment variables:

- `FLASK_ENV`: Set to "development" for debugging
- `REPL_ID`: Replit application ID
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## SSH Key Setup

For server management functionality, mount your SSH keys:

```bash
# Ensure SSH keys exist
ls -la ~/.ssh/

# Keys will be automatically mounted to /root/.ssh in the container
```

## Troubleshooting

### Common Issues

1. **Database connection failed:**
   ```bash
   docker-compose logs db
   # Check if PostgreSQL is running and accepting connections
   ```

2. **Web service won't start:**
   ```bash
   docker-compose logs web
   # Check for Python/Flask errors
   ```

3. **Port already in use:**
   ```bash
   # Change ports in docker-compose.yml or stop conflicting services
   sudo lsof -i :5000
   ```

4. **Permission issues with SSH keys:**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/*
   ```

### Health Checks

```bash
# Check service health
docker-compose ps

# Test web service directly
curl http://localhost:5000/

# Test database connection
docker-compose exec db pg_isready -U dynamic_user
```

## Production Considerations

1. **Security:**
   - Use strong passwords and session secrets
   - Enable SSL/TLS in production
   - Regular security updates

2. **Performance:**
   - Adjust worker count in gunicorn
   - Monitor resource usage
   - Set up log rotation

3. **Backup:**
   - Regular database backups
   - Backup SSH keys securely
   - Version control configuration

4. **Monitoring:**
   - Set up health checks
   - Monitor logs for errors
   - Track resource usage