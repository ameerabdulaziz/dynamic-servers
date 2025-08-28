#!/bin/bash

# Docker Test Script for Dynamic Servers
# This script tests the Docker setup and deployment

set -e  # Exit on any error

echo "🚀 Starting Dynamic Servers Docker Test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env file with your actual values before running in production"
fi

# Build the Docker image
print_status "Building Docker image..."
docker-compose build

# Start the services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 20

# Check if services are running
print_status "Checking service health..."

# Check database
if docker-compose exec -T db pg_isready -U dynamic_user -d dynamic_servers > /dev/null 2>&1; then
    print_success "Database is running and ready"
else
    print_error "Database is not responding"
    docker-compose logs db
    exit 1
fi

# Check web service
if curl -f http://localhost:5000/ > /dev/null 2>&1; then
    print_success "Web service is running and accessible"
else
    print_warning "Web service health check failed, checking logs..."
    docker-compose logs web
fi

# Show running containers
print_status "Container status:"
docker-compose ps

# Show logs
print_status "Recent logs (last 20 lines):"
docker-compose logs --tail=20

print_success "Docker test completed!"
print_status "Access your application at: http://localhost:5000"
print_status "Database connection: postgresql://dynamic_user:dynamic_pass@localhost:5432/dynamic_servers"

echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your actual API keys"
echo "2. Set up your SSH keys for server management"
echo "3. Configure your Hetzner API token"
echo ""
echo "🛠  Useful commands:"
echo "  docker-compose logs -f web    # Follow web service logs"
echo "  docker-compose logs -f db     # Follow database logs"
echo "  docker-compose down           # Stop all services"
echo "  docker-compose restart web    # Restart web service"